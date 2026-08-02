"""
Requirement 5: Database Interaction (SQL Queries + Business Logic).

A terminal/console interface that talks to ecommerce.db (built by init_db.py)
via sqlite3. Lets a user browse the catalog, manage a cart, check out with a
saved payment card (which creates a permanent Order + Order_Item record),
view order history, and run a few reporting queries - including a
multi-table join.
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "ecommerce.db"


def get_connection():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}. Run init_db.py first.")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def print_rows(rows, headers):
    if not rows:
        print("  (no results)")
        return
    widths = [max(len(str(h)), *(len(str(r[i])) for r in rows)) for i, h in enumerate(headers)]
    header_line = " | ".join(h.ljust(w) for h, w in zip(headers, widths))
    print("  " + header_line)
    print("  " + "-" * len(header_line))
    for r in rows:
        print("  " + " | ".join(str(r[i]).ljust(w) for i, w in enumerate(widths)))


# ---------------------------------------------------------------
# Catalog browsing
# ---------------------------------------------------------------

def view_all_products(conn):
    # Each row is one seller's listing of one product (M:N via Seller_Inventory)
    query = """
        SELECT p.PID, p.Product_name, p.Category, s.SID, s.Store_name,
               p.Price, si.Quantity
        FROM Product p
        JOIN Seller_Inventory si ON p.PID = si.PID
        JOIN Seller s ON si.SID = s.SID
        ORDER BY p.PID, s.SID;
    """
    rows = conn.execute(query).fetchall()
    print("\nAll product listings (by seller):")
    print_rows(rows, ["PID", "Product", "Category", "SID", "Seller", "Price", "Qty"])


def browse_by_category(conn):
    cats = conn.execute("SELECT DISTINCT Category FROM Product ORDER BY Category;").fetchall()
    print("\nCategories:")
    for c in cats:
        print(f"  - {c['Category']}")
    cat = input("Enter category name: ").strip()

    query = """
        SELECT p.PID, p.Product_name, p.Price, s.SID, s.Store_name, si.Quantity
        FROM Product p
        JOIN Seller_Inventory si ON p.PID = si.PID
        JOIN Seller s ON si.SID = s.SID
        WHERE p.Category = ? COLLATE NOCASE
        ORDER BY p.Price;
    """
    rows = conn.execute(query, (cat,)).fetchall()
    print_rows(rows, ["PID", "Product", "Price", "SID", "Seller", "Qty"])


# ---------------------------------------------------------------
# Cart / business logic
# ---------------------------------------------------------------

def add_to_cart(conn):
    try:
        bid = int(input("Your Buyer ID: ").strip())
        pid = int(input("Product ID to add: ").strip())
        sid = int(input("Seller ID to buy from (see 'View all products'): ").strip())
        qty = int(input("Quantity: ").strip())
    except ValueError:
        print("Invalid input.")
        return

    buyer = conn.execute("SELECT 1 FROM Buyer WHERE BID = ?;", (bid,)).fetchone()
    if not buyer:
        print("No such buyer.")
        return

    listing = conn.execute(
        "SELECT Quantity FROM Seller_Inventory WHERE SID = ? AND PID = ?;", (sid, pid)
    ).fetchone()
    if not listing:
        print("That seller does not carry this product.")
        return
    if qty <= 0 or qty > listing["Quantity"]:
        print(f"Invalid quantity. Only {listing['Quantity']} in stock from this seller.")
        return

    conn.execute(
        """
        INSERT INTO Cart (BID, SID, PID, Quantity)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(BID, SID, PID) DO UPDATE SET Quantity = Quantity + excluded.Quantity;
        """,
        (bid, sid, pid, qty),
    )
    conn.commit()
    print("Added to cart.")


def view_cart(conn):
    try:
        bid = int(input("Your Buyer ID: ").strip())
    except ValueError:
        print("Invalid input.")
        return

    query = """
        SELECT p.PID, p.Product_name, s.Store_name, ct.Quantity, p.Price,
               (ct.Quantity * p.Price) AS Subtotal
        FROM Cart ct
        JOIN Product p ON ct.PID = p.PID
        JOIN Seller s ON ct.SID = s.SID
        WHERE ct.BID = ?;
    """
    rows = conn.execute(query, (bid,)).fetchall()
    print_rows(rows, ["PID", "Product", "Seller", "Qty", "Price", "Subtotal"])
    if rows:
        total = sum(r["Subtotal"] for r in rows)
        print(f"  Cart total: ${total:.2f}")


def checkout(conn):
    """
    Verifies stock, creates a permanent Order + Order_Item record
    (freezing the price paid), decrements Seller_Inventory, and
    clears the buyer's Cart -- all in one transaction.
    """
    try:
        bid = int(input("Your Buyer ID: ").strip())
    except ValueError:
        print("Invalid input.")
        return

    cards = conn.execute(
        "SELECT CardID, Card_Number, Address FROM Payment_Card WHERE BID = ?;", (bid,)
    ).fetchall()
    if not cards:
        print("No payment card on file for this buyer.")
        return

    print("Payment cards on file:")
    for c in cards:
        print(f"  {c['CardID']}. {c['Card_Number']} -> {c['Address']}")
    try:
        card_id = int(input("Choose CardID to pay with: ").strip())
    except ValueError:
        print("Invalid input.")
        return
    if card_id not in [c["CardID"] for c in cards]:
        print("That card does not belong to this buyer.")
        return

    cart_items = conn.execute(
        """
        SELECT ct.SID, ct.PID, ct.Quantity, p.Price
        FROM Cart ct
        JOIN Product p ON ct.PID = p.PID
        WHERE ct.BID = ?;
        """,
        (bid,),
    ).fetchall()
    if not cart_items:
        print("Cart is empty.")
        return

    # Verify stock per seller listing before committing to anything
    for item in cart_items:
        stock = conn.execute(
            "SELECT Quantity FROM Seller_Inventory WHERE SID = ? AND PID = ?;",
            (item["SID"], item["PID"]),
        ).fetchone()["Quantity"]
        if stock < item["Quantity"]:
            print(f"Insufficient stock for PID {item['PID']} from SID {item['SID']}. Checkout aborted.")
            return

    total = sum(item["Quantity"] * item["Price"] for item in cart_items)

    try:
        cur = conn.execute(
            'INSERT INTO "Order" (BID, CardID, Total) VALUES (?, ?, ?);',
            (bid, card_id, total),
        )
        order_id = cur.lastrowid

        for item in cart_items:
            conn.execute(
                """
                INSERT INTO Order_Item (OrderID, SID, PID, Quantity, Price_at_purchase)
                VALUES (?, ?, ?, ?, ?);
                """,
                (order_id, item["SID"], item["PID"], item["Quantity"], item["Price"]),
            )
            conn.execute(
                "UPDATE Seller_Inventory SET Quantity = Quantity - ? WHERE SID = ? AND PID = ?;",
                (item["Quantity"], item["SID"], item["PID"]),
            )

        conn.execute("DELETE FROM Cart WHERE BID = ?;", (bid,))
        conn.commit()
        print(f"Order #{order_id} placed successfully (${total:.2f}), charged to card {card_id}.")
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Checkout failed: {e}")


def view_order_history(conn):
    try:
        bid = int(input("Your Buyer ID: ").strip())
    except ValueError:
        print("Invalid input.")
        return

    orders = conn.execute(
        'SELECT OrderID, Order_date, Total FROM "Order" WHERE BID = ? ORDER BY Order_date DESC;',
        (bid,),
    ).fetchall()
    if not orders:
        print("  (no past orders)")
        return

    for o in orders:
        print(f"\nOrder #{o['OrderID']} -- {o['Order_date']} -- Total: ${o['Total']:.2f}")
        items = conn.execute(
            """
            SELECT p.Product_name, s.Store_name, oi.Quantity, oi.Price_at_purchase
            FROM Order_Item oi
            JOIN Product p ON oi.PID = p.PID
            JOIN Seller s ON oi.SID = s.SID
            WHERE oi.OrderID = ?;
            """,
            (o["OrderID"],),
        ).fetchall()
        print_rows(items, ["Product", "Seller", "Qty", "Price_at_purchase"])


# ---------------------------------------------------------------
# Requirement 5a: at least 3 SQL queries, one multi-table
# ---------------------------------------------------------------

def query_products_with_sellers(conn):
    # Multi-table query #1: Display product information sorted by seller
    query = """
        SELECT p.Product_name, s.Store_name, p.Category, p.Price, si.Quantity
        FROM Product p
        JOIN Seller_Inventory si ON p.PID = si.PID
        JOIN Seller s ON si.SID = s.SID
        ORDER BY s.Store_name DESC;
    """
    rows = conn.execute(query).fetchall()
    print("\nAll products information sorted by Seller:")
    print_rows(rows, ["Product", "Seller", "Category", "Price", "Qty"])


def query_buyers_and_expensive_cart_items(conn):
    # Multi-table query #2:
    # buyer names alongside product names in their cart, price > $100
    query = """
        SELECT b.Name AS Buyer_Name, p.Product_name, s.Store_name, p.Price
        FROM Buyer b
        JOIN Cart ct ON b.BID = ct.BID
        JOIN Product p ON ct.PID = p.PID
        JOIN Seller s ON ct.SID = s.SID
        WHERE p.Price > 100
        ORDER BY p.Price DESC;
    """
    rows = conn.execute(query).fetchall()
    print("\nBuyers with cart items priced over $100:")
    print_rows(rows, ["Buyer", "Product", "Seller", "Price"])


def query_order_totals_per_buyer(conn):
    # Multi-table query #3: total spend per buyer across all orders
    query = """
        SELECT b.Name AS Buyer_Name, COUNT(o.OrderID) AS Num_Orders,
               COALESCE(SUM(o.Total), 0) AS Total_Spent
        FROM Buyer b
        LEFT JOIN "Order" o ON b.BID = o.BID
        GROUP BY b.BID
        ORDER BY Total_Spent DESC;
    """
    rows = conn.execute(query).fetchall()
    print("\nTotal spend per buyer:")
    rows_fmt = [(r["Buyer_Name"], r["Num_Orders"], f"{r['Total_Spent']:.2f}") for r in rows]
    print_rows(rows_fmt, ["Buyer", "Num_Orders", "Total_Spent"])


def query_products_per_category(conn):
    query = """
        SELECT Category, COUNT(*) AS Num_Products, AVG(Price) AS Avg_Price
        FROM Product
        GROUP BY Category
        ORDER BY Num_Products DESC;
    """
    rows = conn.execute(query).fetchall()
    print("\nProduct count and average price per category:")
    rows_fmt = [(r["Category"], r["Num_Products"], f"{r['Avg_Price']:.2f}") for r in rows]
    print_rows(rows_fmt, ["Category", "Num_Products", "Avg_Price"])


def run_sample_queries(conn):
    query_products_with_sellers(conn)
    query_buyers_and_expensive_cart_items(conn)
    query_order_totals_per_buyer(conn)
    query_products_per_category(conn)


# ---------------------------------------------------------------
# Menu
# ---------------------------------------------------------------

MENU = """
==== Happy to assist with your shopping today! ====
1. View all products (by seller)
2. Browse products by category
3. Add product to cart
4. View my cart
5. Checkout
6. View order history
7. Run sample SQL reports 
0. Exit
"""


def main():
    conn = get_connection()
    actions = {
        "1": view_all_products,
        "2": browse_by_category,
        "3": add_to_cart,
        "4": view_cart,
        "5": checkout,
        "6": view_order_history,
        "7": run_sample_queries,
    }
    try:
        while True:
            print(MENU)
            choice = input("Choose an option: ").strip()
            if choice == "0":
                print("Thank you for shopping!")
                break
            action = actions.get(choice)
            if action:
                action(conn)
            else:
                print("Invalid option.")
    except KeyboardInterrupt:
        print("\nThank you for shopping!")
    finally:
        conn.close()


if __name__ == "__main__":
    main()