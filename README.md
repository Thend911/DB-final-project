# 1. Problem statement & requirements

In this project, I am stimulating a basic E-commerce platform. In this platform there are serveral things that need to be defnied first:
* Seller : A person who sells different products on the platform
* Product : An object that are sold by a seller and are bought by a buyer
* Buyer : A person who buys product sold on platform

Requirements:
* Product Catalog: Easy sorting, categories, high-resolution images, and stock tracking.
* Shopping Cart & Checkout: Fast loading, guest checkout options, and a progress bar.
* Payment Integration: Secure processors like Stripe or PayPal supporting credit cards and express digital wallets.
* Order Management: Tools to track customer purchases, handle refunds, and update shipping details 
* Speed & Performance: Fast page load times to prevent high bounce rates and lost sales.
* Security & Compliance: PCI-compliance to protect user data and financial transactions safely.
* Scalability: Ability to grow smoothly and handle higher visitor traffic as the business expands.
* Integrations: Seamless connection options for inventory, marketing tools, and accounting software.

## Identify the Entities
### **Strong entities**

<table>
<tr>
<th style="border-right: 1px solid #ccc; padding: 10px;">1. Buyer</th>
<th style="border-right: 1px solid #ccc; padding: 10px;">2. Seller</th>
<th style="padding: 10px;">3. Product</th>
</tr>
<tr>
<td valign="top" style="border-right: 1px solid #ccc; padding: 10px;">

|Column|Keys|
|---|---|
|BID|PK|
|Name||

</td>
<td valign="top" style="border-right: 1px solid #ccc; padding: 10px;">

|Column|Keys|
|---|---|
|SID|PK|
|Store_name||
|Email||
|Phone||

</td>
<td valign="top" style="padding: 10px;">

|Column|Keys|
|---|---|
|PID|PK|
|SID|FK|
|Product_name||
|Price||
|Quantity||

</td>
</tr>
</table>

### **Weak entitnies**

<table>
<tr>
<th style="border-right: 1px solid #ccc; padding: 10px;">1. Buyer contact</th>
<th style="border-right: 1px solid #ccc; padding: 10px;">2. Seller inventory</th>
<th style="padding: 10px;">3. Product</th>
</tr>
<tr>
<td valign="top" style="border-right: 1px solid #ccc; padding: 10px;">

|Column|Keys|
|---|---|
|BID|FK|
|Email||
|Address||
|Phone||

</td>
<td valign="top" style="border-right: 1px solid #ccc; padding: 10px;">

|Column|Keys|
|---|---|
|SID|FK|
|PID|FK|

</td>
<td valign="top" style="padding: 10px;">

|Column|Keys|
|---|---|
|PID|FK|
|SID|FK|
|Product_name||
|Price||
|Quantity||

</td>
</tr>
</table>
# 2. 