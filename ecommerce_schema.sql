-- ============================================================
-- E-Commerce Platform Relational Schema
-- Requirement 4: Schema creation + sample INSERT statements
-- Engine: SQLite (portable to MySQL/PostgreSQL with minor tweaks)
-- ============================================================

PRAGMA foreign_keys = ON;

-- Drop tables if re-running this script (reverse dependency order)
DROP TABLE IF EXISTS Order_Item;
DROP TABLE IF EXISTS "Order";
DROP TABLE IF EXISTS Cart;
DROP TABLE IF EXISTS Payment_Card;
DROP TABLE IF EXISTS Seller_Inventory;
DROP TABLE IF EXISTS Product;
DROP TABLE IF EXISTS Buyer;
DROP TABLE IF EXISTS Seller;

-- ------------------------------------------------------------
-- Strong entity: Seller
-- ------------------------------------------------------------
CREATE TABLE Seller (
    SID         INTEGER PRIMARY KEY AUTOINCREMENT,
    Store_name  TEXT NOT NULL,
    Email       TEXT NOT NULL UNIQUE,
    Phone       TEXT
);

-- ------------------------------------------------------------
-- Strong entity: Buyer
-- ------------------------------------------------------------
CREATE TABLE Buyer (
    BID   INTEGER PRIMARY KEY AUTOINCREMENT,
    Name  TEXT NOT NULL
);

-- ------------------------------------------------------------
-- Strong entity: Product
-- ------------------------------------------------------------
CREATE TABLE Product (
    PID           INTEGER PRIMARY KEY AUTOINCREMENT,
    Product_name  TEXT NOT NULL,
    Category      TEXT NOT NULL,
    Price         REAL NOT NULL CHECK (Price >= 0)
);

-- ------------------------------------------------------------
-- Relationship-with-attribute: Seller_Inventory
-- Resolves the M:N relationship between Seller and Product.
-- Key is fully composed of the two FKs (SID, PID)
-- ------------------------------------------------------------
CREATE TABLE Seller_Inventory (
    SID       INTEGER NOT NULL,
    PID       INTEGER NOT NULL,
    Quantity  INTEGER NOT NULL DEFAULT 0 CHECK (Quantity >= 0),
    PRIMARY KEY (SID, PID),
    FOREIGN KEY (SID) REFERENCES Seller(SID) ON DELETE CASCADE,
    FOREIGN KEY (PID) REFERENCES Product(PID) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- Weak entity: Payment_Card
-- Each card has exactly one address and one phone number.
-- ------------------------------------------------------------
CREATE TABLE Payment_Card (
    CardID       INTEGER PRIMARY KEY AUTOINCREMENT,
    BID          INTEGER NOT NULL,
    Card_Number  TEXT NOT NULL,
    Address      TEXT NOT NULL,
    Phone        TEXT NOT NULL,
    FOREIGN KEY (BID) REFERENCES Buyer(BID) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- Relationship-with-attribute: Cart
-- Resolves the M:N relationship between Buyer and Seller_Inventory
-- (a buyer can add "Product X from Seller A" and "Product X from
-- Seller B" as two distinct lines). Cleared out at checkout, when
-- its contents are copied into Order_Item.
-- ------------------------------------------------------------
CREATE TABLE Cart (
    BID       INTEGER NOT NULL,
    SID       INTEGER NOT NULL,
    PID       INTEGER NOT NULL,
    Quantity  INTEGER NOT NULL DEFAULT 1 CHECK (Quantity > 0),
    PRIMARY KEY (BID, SID, PID),
    FOREIGN KEY (BID) REFERENCES Buyer(BID) ON DELETE CASCADE,
    FOREIGN KEY (SID, PID) REFERENCES Seller_Inventory(SID, PID) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- Strong entity: Order
-- Has its own surrogate key; permanent record created at checkout.
-- ------------------------------------------------------------
CREATE TABLE "Order" (
    OrderID     INTEGER PRIMARY KEY AUTOINCREMENT,
    BID         INTEGER NOT NULL,
    CardID      INTEGER NOT NULL,
    Order_date  TEXT NOT NULL DEFAULT (datetime('now')),
    Total       REAL NOT NULL CHECK (Total >= 0),
    FOREIGN KEY (BID) REFERENCES Buyer(BID),
    FOREIGN KEY (CardID) REFERENCES Payment_Card(CardID)
);

-- ------------------------------------------------------------
-- Relationship-with-attribute: Order_Item
-- Resolves the M:N relationship between Order and Seller_Inventory.
-- Price_at_purchase freezes the price paid, since Product.Price
-- may change later.
-- ------------------------------------------------------------
CREATE TABLE Order_Item (
    OrderID            INTEGER NOT NULL,
    SID                INTEGER NOT NULL,
    PID                INTEGER NOT NULL,
    Quantity           INTEGER NOT NULL CHECK (Quantity > 0),
    Price_at_purchase  REAL NOT NULL CHECK (Price_at_purchase >= 0),
    PRIMARY KEY (OrderID, SID, PID),
    FOREIGN KEY (OrderID) REFERENCES "Order"(OrderID) ON DELETE CASCADE,
    FOREIGN KEY (SID, PID) REFERENCES Seller_Inventory(SID, PID)
);

-- ============================================================
-- Sample data
-- ============================================================

INSERT INTO Seller (Store_name, Email, Phone) VALUES
    ('TechNest',      'contact@technest.com',    '555-0101'),
    ('Urban Threads', 'hello@urbanthreads.com',  '555-0102'),
    ('HomeGoods Co',  'sales@homegoodsco.com',   '555-0103');

INSERT INTO Buyer (Name) VALUES
    ('Alice Johnson'),
    ('Brian Lee'),
    ('Carla Gomez');

INSERT INTO Product (Product_name, Category, Price) VALUES
    ('Wireless Mouse',        'Electronics',    24.99),
    ('Mechanical Keyboard',   'Electronics',   129.99),
    ('4K Monitor',            'Electronics',   329.00),
    ('Denim Jacket',          'Clothing',       89.50),
    ('Cotton T-Shirt',        'Clothing',       19.99),
    ('Running Shoes',         'Clothing',      109.99),
    ('Non-stick Pan Set',     'Home & Kitchen',145.00),
    ('Coffee Maker',          'Home & Kitchen', 79.99),
    ('SQL Fundamentals Book', 'Books',          34.95),
    ('Data Design Handbook',  'Books',          42.00);

-- Seller_Inventory: who stocks what, and how much.
-- Wireless Mouse (PID 1) is deliberately carried by two sellers
-- to demonstrate the M:N Seller<->Product relationship.
INSERT INTO Seller_Inventory (SID, PID, Quantity) VALUES
    (1, 1, 150),  -- TechNest: Wireless Mouse
    (1, 2, 80),   -- TechNest: Mechanical Keyboard
    (1, 3, 40),   -- TechNest: 4K Monitor
    (2, 1, 50),   -- Urban Threads also carries Wireless Mouse
    (2, 4, 100),  -- Urban Threads: Denim Jacket
    (2, 5, 300),  -- Urban Threads: Cotton T-Shirt
    (2, 6, 75),   -- Urban Threads: Running Shoes
    (3, 7, 60),   -- HomeGoods Co: Non-stick Pan Set
    (3, 8, 90),   -- HomeGoods Co: Coffee Maker
    (3, 9, 120),  -- HomeGoods Co: SQL Fundamentals Book
    (3, 10, 65);  -- HomeGoods Co: Data Design Handbook

INSERT INTO Payment_Card (BID, Card_Number, Address, Phone) VALUES
    (1, '4111-1111-1111-1111', '12 Maple St, Springfield',   '555-0201'),
    (1, '4222-2222-2222-2222', '90 Oak Ave, Springfield',    '555-0202'),
    (2, '4333-3333-3333-3333', '48 Birch Rd, Rivertown',     '555-0203'),
    (3, '4444-4444-4444-4444', '7 Cedar Ln, Lakeview',       '555-0204');

INSERT INTO Cart (BID, SID, PID, Quantity) VALUES
    (1, 1, 2, 1),   -- Alice: Mechanical Keyboard from TechNest
    (1, 1, 3, 3),   -- Alice: 4K Monitor x3 from TechNest
    (2, 2, 6, 2);   -- Brian: Running Shoes x2 from Urban Threads
    
-- Sample completed order (Brian previously bought a Coffee Maker),
-- to demonstrate Order / Order_Item / Paid_with before any checkout
-- is run through the CLI.
INSERT INTO "Order" (BID, CardID, Order_date, Total) VALUES
    (2, 3, '2026-07-20 10:15:00', 79.99);

INSERT INTO Order_Item (OrderID, SID, PID, Quantity, Price_at_purchase) VALUES
    (1, 3, 8, 1, 79.99);

-- Reflect that this historical order already consumed stock
UPDATE Seller_Inventory SET Quantity = Quantity - 1 WHERE SID = 3 AND PID = 8;