# 1. Problem statement & requirements

In this project, I am simulating a basic E-commerce platform. In this platform there are several things that need to be defined first:
* Seller: A person who sells different products on the platform
* Product: An object that is sold by a seller and bought by a buyer
* Buyer: A person who buys products sold on the platform

Requirements:
* Product Catalog: Easy sorting, categories.
* Shopping Cart & Viewing: Viewing products or add product into shopping cart.
* Payment: Can add multiple card but each corresponding to 1 address and 1 phone number.
* Order History: Every completed checkout is recorded permanently, including which card was charged and the price paid at the time of purchase.

Use Case:
* Seller wants to sell products
* Buyer wants to buy products of some category
* A product may be carried by more than one seller, each with their own stock level (marketplace model)
* A buyer's cart, once checked out, becomes a permanent order record

# 2. Identify the Entities and Relationships

## Strong entities

### Buyer

| Column | Keys |
|---|---|
| BID | PK |
| Name | |
---

### Seller

| Column | Keys |
|---|---|
| SID | PK |
| Store_name | |
| Email | |
| Phone | |
---

### Product

| Column | Keys |
|---|---|
| PID | PK |
| Product_name | |
| Category | |
| Price | |
---

### Order

| Column | Keys |
|---|---|
| OrderID | PK |
| BID | FK |
| CardID | FK |
| Order_date | |
| Total | |
---

## Weak entities

### Payment_Card

| Column | Keys |
|---|---|
| CardID | PK (partial key) |
| BID | FK |
| Card_Number | |
| Address | |
| Phone | |

## Relationships


| # | Relationship name | Cardinality | Participants | Attributes | Notes |
|---|---|---|---|---|---|
| 1 | **Seller_Inventory** | M:N | Seller &harr; Product | (SID FK, PID FK, Quantity, PRIMARY KEY(SID, PID)) |Relationship-with-attribute (`Quantity`). A seller can stock many products; a product can be stocked by many sellers. |
| 2 | **Owns** | 1:N | Buyer &rarr; Payment_Card | |A `Buyer` can have many `Payment_Card` but each `Payment_Card` can have 1 `Buyer`. |
| 3 | **Cart** | M:N | Buyer &harr; Seller_Inventory | (BID FK, SID FK, PID FK, Quantity, PRIMARY KEY(BID, SID, PID), FOREIGN KEY(SID, PID) REFERENCES Seller_Inventory(SID, PID)) | A `Seller` can sell to many different `Buyer`, vice versa. Each line references one buyer and one specific seller's listing. |
| 4 | **Places** | 1:N | Buyer &rarr; Order || A `Buyer` can place many `Order`; each `order` belongs to exactly one `buyer`. |
| 5 | **Paid_with** | N:1 | Order &rarr; Payment_Card || Each `Order` is charged to exactly one of the buyer's `Payment_Card` but a Buyer's `Payment_Card` can buy many `Order`. |
| 6 | **Order_Item** | M:N | Order &harr; Seller_Inventory | (OrderID FK, SID FK, PID FK, Quantity, Price_at_purchase,PRIMARY KEY(OrderID, SID, PID), FOREIGN KEY(SID, PID) REFERENCES Seller_Inventory(SID, PID))| Buyer can have many `Order` from many `Seller_Inventory` and vice versa. Permanent record of what `Cart` looked like at checkout. |

### Entity-Relationship summary 

![Draw](model.png)

## Relational Schemas

```
Buyer(BID PK, Name)
Seller(SID PK, Store_name, Email, Phone)
Product(PID PK, Product_name, Category, Price)
Seller_Inventory(SID FK, PID FK, Quantity, PRIMARY KEY(SID, PID))
Payment_Card(CardID PK, BID FK, Card_Number, Address, Phone)
Cart(BID FK, SID FK, PID FK, Quantity, PRIMARY KEY(BID, SID, PID),
     FOREIGN KEY(SID, PID) REFERENCES Seller_Inventory(SID, PID))
Order(OrderID PK, BID FK, CardID FK, Order_date, Total)
Order_Item(OrderID FK, SID FK, PID FK, Quantity, Price_at_purchase,
           PRIMARY KEY(OrderID, SID, PID),
           FOREIGN KEY(SID, PID) REFERENCES Seller_Inventory(SID, PID))
```
