# SmartCart — Online Store Management System

SmartCart is a desktop-based online store management application built using Python, Tkinter, and MySQL.

## Features

- Product catalog with search by product name or category
- Shopping cart with quantity updates and item removal
- Checkout with Cash on Delivery
- MySQL storage for orders, order items, and payment records
- Inventory and stock management
- Admin dashboard to add products, delete eligible products, and update stock
- Order history with order details

## Tech Stack

- Python 3
- Tkinter
- MySQL
- MySQL Connector/Python

## Prerequisites

- Python 3.x
- MySQL Server
- `mysql-connector-python`

## Setup and Installation

1. Download or clone this repository.
2. Make sure MySQL Server is running.
3. Install the required Python package:

   ```bash
   pip install -r requirements.txt
   ```

4. Open `smartcart_updated.py` and update the MySQL connection settings to match your local MySQL configuration.
5. Run the application:

   ```bash
   python smartcart_updated.py
   ```

The application creates the `smartcart_db` database and its required tables when it connects successfully to MySQL. Sample products are inserted if the product catalog is empty.

## Database Tables

- `products` — product details, prices, and available stock
- `orders` — customer and order summary information
- `order_items` — products included in each order
- `payments` — payment method and payment status

## Future Improvements

- User login and authentication
- Online payment gateway integration
- Persistent shopping carts
- Sales analytics and reports
- AI-based product recommendations

## Project Type

Academic team project.
