
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import mysql.connector
from mysql.connector import Error
from decimal import Decimal

# =====================================================
# 1. MYSQL CONNECTION AND DATABASE CREATION
# =====================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "admin"
}

DB_NAME = "smartcart_db"


def connect_database():
    """Create database if necessary and connect to it."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        cursor.close()
        conn.close()

        conn = mysql.connector.connect(
            **DB_CONFIG,
            database=DB_NAME
        )

        if conn.is_connected():
            print("Connection established...")
            return conn

    except Error as e:
        messagebox.showerror(
            "Database Connection Error",
            f"Could not connect to MySQL.\n\n{e}\n\n"
            "Check that MySQL is running and the root password is correct."
        )

    return None


conn = connect_database()

if conn is None:
    raise SystemExit("SmartCart cannot start without MySQL.")


# =====================================================
# 2. CREATE TABLES
# =====================================================

def create_tables():
    cursor = conn.cursor()

    queries = [
        """
        CREATE TABLE IF NOT EXISTS products (
            product_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            category VARCHAR(60) NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            stock INT NOT NULL DEFAULT 0,
            CHECK (price > 0),
            CHECK (stock >= 0)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS orders (
            order_id INT AUTO_INCREMENT PRIMARY KEY,
            customer_name VARCHAR(100) NOT NULL,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_amount DECIMAL(12,2) NOT NULL,
            status VARCHAR(30) DEFAULT 'Placed'
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS order_items (
            item_id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT NOT NULL,
            product_id INT NOT NULL,
            product_name VARCHAR(100) NOT NULL,
            quantity INT NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id),
            CHECK (quantity > 0)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS payments (
            payment_id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT NOT NULL,
            amount DECIMAL(12,2) NOT NULL,
            method VARCHAR(30) NOT NULL DEFAULT 'Cash on Delivery',
            payment_status VARCHAR(30) NOT NULL DEFAULT 'Pending',
            FOREIGN KEY (order_id) REFERENCES orders(order_id)
        )
        """
    ]

    try:
        for query in queries:
            cursor.execute(query)

        conn.commit()

        # Insert sample products only when the catalog is empty.
        cursor.execute("SELECT COUNT(*) FROM products")

        if cursor.fetchone()[0] == 0:
            sample_products = [
                ("Laptop", "Electronics", 45000, 5),
                ("Headphones", "Electronics", 1500, 10),
                ("Backpack", "Fashion", 900, 8),
                ("T-Shirt", "Fashion", 500, 15),
                ("Smart Watch", "Electronics", 2500, 6)
            ]

            cursor.executemany(
                """
                INSERT INTO products (name, category, price, stock)
                VALUES (%s, %s, %s, %s)
                """,
                sample_products
            )
            conn.commit()

    except Error as e:
        conn.rollback()
        messagebox.showerror("Database Setup Error", str(e))
        raise

    finally:
        cursor.close()


create_tables()


# =====================================================
# 3. DATABASE HELPER FUNCTIONS
# =====================================================

def fetch_all(query, params=()):
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        cursor.close()


def execute_query(query, params=()):
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()
        return cursor.lastrowid
    except Error:
        conn.rollback()
        raise
    finally:
        cursor.close()


# Cart format: {product_id: quantity}
cart = {}


# =====================================================
# 4. MAIN WINDOW
# =====================================================

root = tk.Tk()
root.title("SmartCart - Online Store Management System")
root.geometry("1000x650")
root.minsize(800, 500)
root.configure(bg="#f1f5f9")

style = ttk.Style()
style.theme_use("clam")
style.configure(
    "Treeview",
    rowheight=30,
    font=("Arial", 10)
)
style.configure(
    "Treeview.Heading",
    font=("Arial", 10, "bold")
)

header = tk.Frame(root, bg="#12345a", height=70)
header.pack(fill="x")

tk.Label(
    header,
    text="SmartCart",
    font=("Arial", 23, "bold"),
    bg="#12345a",
    fg="white"
).pack(side="left", padx=25, pady=15)

tk.Label(
    header,
    text="Online Store Management System",
    font=("Arial", 11),
    bg="#12345a",
    fg="white"
).pack(side="right", padx=20)

nav = tk.Frame(root, bg="#dbeafe")
nav.pack(fill="x")

content = tk.Frame(root, bg="#f1f5f9")
content.pack(fill="both", expand=True, padx=20, pady=15)


def clear_content():
    for widget in content.winfo_children():
        widget.destroy()


def make_button(parent, text, command):
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg="#2563eb",
        fg="white",
        activebackground="#1d4ed8",
        activeforeground="white",
        font=("Arial", 10, "bold"),
        relief="flat",
        padx=12,
        pady=7,
        cursor="hand2"
    )


def heading(text):
    tk.Label(
        content,
        text=text,
        font=("Arial", 20, "bold"),
        bg="#f1f5f9",
        fg="#12345a"
    ).pack(anchor="w", pady=(0, 12))


# =====================================================
# 5. PRODUCT CATALOG AND SEARCH
# =====================================================

def show_products():
    clear_content()
    heading("Product Catalog")

    search_var = tk.StringVar()

    search_row = tk.Frame(content, bg="#f1f5f9")
    search_row.pack(fill="x", pady=(0, 10))

    tk.Label(
        search_row,
        text="Search name/category:",
        bg="#f1f5f9"
    ).pack(side="left")

    ttk.Entry(
        search_row,
        textvariable=search_var,
        width=35
    ).pack(side="left", padx=8)

    columns = ("ID", "Name", "Category", "Price (Rs.)", "Stock")
    tree = ttk.Treeview(
        content,
        columns=columns,
        show="headings",
        selectmode="browse"
    )

    widths = (70, 220, 180, 150, 100)

    for col, width in zip(columns, widths):
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=width)

    tree.pack(fill="both", expand=True)

    def refresh_products(*args):
        tree.delete(*tree.get_children())

        term = search_var.get().strip()

        try:
            rows = fetch_all(
                """
                SELECT product_id, name, category, price, stock
                FROM products
                WHERE name LIKE %s OR category LIKE %s
                ORDER BY product_id
                """,
                (f"%{term}%", f"%{term}%")
            )

            for p in rows:
                tree.insert(
                    "",
                    "end",
                    values=(
                        p["product_id"],
                        p["name"],
                        p["category"],
                        f'{p["price"]:,.2f}',
                        p["stock"]
                    )
                )

        except Error as e:
            messagebox.showerror("Database Error", str(e))

    def add_to_cart():
        selected = tree.selection()

        if not selected:
            messagebox.showwarning(
                "Select Product",
                "Please select a product first."
            )
            return

        product_id = int(tree.item(selected[0], "values")[0])

        try:
            rows = fetch_all(
                "SELECT stock, name FROM products WHERE product_id = %s",
                (product_id,)
            )

            if not rows:
                messagebox.showerror(
                    "Not Found",
                    "This product no longer exists."
                )
                refresh_products()
                return

            product = rows[0]

            if cart.get(product_id, 0) >= product["stock"]:
                messagebox.showwarning(
                    "Out of Stock",
                    "No more stock is available."
                )
                return

            cart[product_id] = cart.get(product_id, 0) + 1

            messagebox.showinfo(
                "SmartCart",
                f'{product["name"]} added to cart!'
            )

        except Error as e:
            messagebox.showerror("Database Error", str(e))

    search_var.trace_add("write", refresh_products)
    refresh_products()

    make_button(
        content,
        "Add Selected Product to Cart",
        add_to_cart
    ).pack(anchor="e", pady=12)


# =====================================================
# 6. SHOPPING CART
# =====================================================

def show_cart():
    clear_content()
    heading("Shopping Cart")

    columns = (
        "ID",
        "Name",
        "Price (Rs.)",
        "Quantity",
        "Subtotal (Rs.)"
    )

    tree = ttk.Treeview(
        content,
        columns=columns,
        show="headings",
        selectmode="browse"
    )

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=150)

    tree.pack(fill="both", expand=True)

    total_label = tk.Label(
        content,
        text="",
        font=("Arial", 15, "bold"),
        bg="#f1f5f9",
        fg="#12345a"
    )
    total_label.pack(anchor="e", pady=12)

    def refresh_cart():
        tree.delete(*tree.get_children())
        total = Decimal("0.00")

        try:
            for product_id, quantity in list(cart.items()):
                rows = fetch_all(
                    """
                    SELECT product_id, name, price, stock
                    FROM products
                    WHERE product_id = %s
                    """,
                    (product_id,)
                )

                if not rows:
                    cart.pop(product_id, None)
                    continue

                p = rows[0]
                subtotal = p["price"] * quantity
                total += subtotal

                tree.insert(
                    "",
                    "end",
                    iid=str(product_id),
                    values=(
                        p["product_id"],
                        p["name"],
                        f'{p["price"]:,.2f}',
                        quantity,
                        f'{subtotal:,.2f}'
                    )
                )

            total_label.config(text=f"Total: Rs. {total:,.2f}")

        except Error as e:
            messagebox.showerror("Database Error", str(e))

    def remove_item():
        selected = tree.selection()

        if not selected:
            messagebox.showwarning(
                "Select Item",
                "Select an item to remove."
            )
            return

        cart.pop(int(selected[0]), None)
        refresh_cart()

    def change_quantity():
        selected = tree.selection()

        if not selected:
            messagebox.showwarning(
                "Select Item",
                "Select a product first."
            )
            return

        product_id = int(selected[0])

        quantity = simpledialog.askinteger(
            "Update Quantity",
            "Enter the new quantity (0 to remove):",
            minvalue=0,
            parent=root
        )

        if quantity is None:
            return

        if quantity == 0:
            cart.pop(product_id, None)
            refresh_cart()
            return

        try:
            rows = fetch_all(
                "SELECT stock FROM products WHERE product_id = %s",
                (product_id,)
            )

            if not rows:
                cart.pop(product_id, None)
                refresh_cart()
                return

            if quantity > rows[0]["stock"]:
                messagebox.showwarning(
                    "Insufficient Stock",
                    f'Only {rows[0]["stock"]} units are available.'
                )
                return

            cart[product_id] = quantity
            refresh_cart()

        except Error as e:
            messagebox.showerror("Database Error", str(e))

    def checkout():
        if not cart:
            messagebox.showwarning(
                "Empty Cart",
                "Add products before checkout."
            )
            return

        customer_name = simpledialog.askstring(
            "Checkout",
            "Enter customer name:",
            parent=root
        )

        if not customer_name or not customer_name.strip():
            return

        customer_name = customer_name.strip()
        cursor = conn.cursor(dictionary=True)

        try:
            # Earlier SELECT queries may have opened an implicit transaction
            # because MySQL Connector/Python uses autocommit=False by default.
            # End that read transaction before starting checkout's transaction.
            if conn.in_transaction:
                conn.rollback()

            # Keep order creation and stock updates in one transaction.
            conn.start_transaction()

            order_lines = []
            total = Decimal("0.00")

            for product_id, quantity in cart.items():
                cursor.execute(
                    """
                    SELECT product_id, name, price, stock
                    FROM products
                    WHERE product_id = %s
                    FOR UPDATE
                    """,
                    (product_id,)
                )

                p = cursor.fetchone()

                if not p:
                    raise ValueError(
                        f"Product ID {product_id} no longer exists."
                    )

                if quantity <= 0 or p["stock"] < quantity:
                    raise ValueError(
                        f'Insufficient stock for {p["name"]}. '
                        f'Available stock: {p["stock"]}.'
                    )

                subtotal = p["price"] * quantity
                total += subtotal

                order_lines.append({
                    "product_id": p["product_id"],
                    "name": p["name"],
                    "price": p["price"],
                    "quantity": quantity
                })

            if not messagebox.askyesno(
                "Confirm Order",
                f"Customer: {customer_name}\n"
                f"Total: Rs. {total:,.2f}\n\n"
                "Place this order using Cash on Delivery?",
                parent=root
            ):
                conn.rollback()
                return

            cursor.execute(
                """
                INSERT INTO orders
                    (customer_name, total_amount, status)
                VALUES (%s, %s, %s)
                """,
                (customer_name, total, "Placed")
            )

            order_id = cursor.lastrowid

            for item in order_lines:
                cursor.execute(
                    """
                    INSERT INTO order_items
                        (order_id, product_id, product_name,
                         quantity, price)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        order_id,
                        item["product_id"],
                        item["name"],
                        item["quantity"],
                        item["price"]
                    )
                )

                cursor.execute(
                    """
                    UPDATE products
                    SET stock = stock - %s
                    WHERE product_id = %s AND stock >= %s
                    """,
                    (
                        item["quantity"],
                        item["product_id"],
                        item["quantity"]
                    )
                )

                if cursor.rowcount != 1:
                    raise ValueError(
                        f'Could not update stock for {item["name"]}.'
                    )

            cursor.execute(
                """
                INSERT INTO payments
                    (order_id, amount, method, payment_status)
                VALUES (%s, %s, %s, %s)
                """,
                (order_id, total, "Cash on Delivery", "Pending")
            )

            conn.commit()
            cart.clear()
            refresh_cart()

            messagebox.showinfo(
                "Order Placed",
                f"Order #{order_id} placed successfully!\n"
                f"Total: Rs. {total:,.2f}\n"
                "Payment: Cash on Delivery (Pending)"
            )

        except (Error, ValueError) as e:
            conn.rollback()
            messagebox.showerror(
                "Checkout Failed",
                str(e)
            )

        finally:
            cursor.close()

    buttons = tk.Frame(content, bg="#f1f5f9")
    buttons.pack(fill="x", pady=5)

    make_button(
        buttons, "Remove Item", remove_item
    ).pack(side="left", padx=(0, 8))

    make_button(
        buttons, "Change Quantity", change_quantity
    ).pack(side="left", padx=8)

    make_button(
        buttons, "Checkout", checkout
    ).pack(side="right")

    refresh_cart()


# =====================================================
# 7. ADMIN PRODUCT MANAGEMENT
# =====================================================

def show_admin():
    clear_content()
    heading("Admin Dashboard")

    tk.Label(
        content,
        text="Manage the MySQL product catalog.",
        font=("Arial", 11),
        bg="#f1f5f9"
    ).pack(anchor="w", pady=5)

    def add_product():
        name = simpledialog.askstring(
            "New Product", "Product name:", parent=root
        )

        if not name or not name.strip():
            return

        category = simpledialog.askstring(
            "New Product", "Category:", parent=root
        )

        if not category or not category.strip():
            return

        price = simpledialog.askfloat(
            "New Product",
            "Price (Rs.):",
            minvalue=0.01,
            parent=root
        )

        if price is None:
            return

        stock = simpledialog.askinteger(
            "New Product",
            "Stock quantity:",
            minvalue=0,
            parent=root
        )

        if stock is None:
            return

        try:
            execute_query(
                """
                INSERT INTO products (name, category, price, stock)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    name.strip(),
                    category.strip(),
                    price,
                    stock
                )
            )

            messagebox.showinfo(
                "SmartCart",
                "Product added to MySQL successfully."
            )

        except Error as e:
            messagebox.showerror("Database Error", str(e))

    def delete_product():
        product_id = simpledialog.askinteger(
            "Delete Product",
            "Enter product ID:",
            minvalue=1,
            parent=root
        )

        if product_id is None:
            return

        try:
            rows = fetch_all(
                "SELECT name FROM products WHERE product_id = %s",
                (product_id,)
            )

            if not rows:
                messagebox.showerror(
                    "Not Found",
                    "Product ID does not exist."
                )
                return

            # Keep products that appear in previous orders for history.
            used = fetch_all(
                "SELECT item_id FROM order_items WHERE product_id = %s LIMIT 1",
                (product_id,)
            )

            if used:
                messagebox.showwarning(
                    "Cannot Delete",
                    "This product is present in order history. "
                    "Keep it to preserve historical records."
                )
                return

            if product_id in cart:
                cart.pop(product_id)

            if not messagebox.askyesno(
                "Confirm Delete",
                f'Delete "{rows[0]["name"]}"?',
                parent=root
            ):
                return

            execute_query(
                "DELETE FROM products WHERE product_id = %s",
                (product_id,)
            )

            messagebox.showinfo(
                "SmartCart",
                "Product deleted successfully."
            )

        except Error as e:
            messagebox.showerror("Database Error", str(e))

    def update_stock():
        product_id = simpledialog.askinteger(
            "Update Stock", "Enter product ID:",
            minvalue=1, parent=root
        )

        if product_id is None:
            return

        stock = simpledialog.askinteger(
            "Update Stock", "Enter new stock quantity:",
            minvalue=0, parent=root
        )

        if stock is None:
            return

        try:
            execute_query(
                "UPDATE products SET stock = %s WHERE product_id = %s",
                (stock, product_id)
            )
            messagebox.showinfo("SmartCart", "Stock updated if the ID exists.")

        except Error as e:
            messagebox.showerror("Database Error", str(e))

    make_button(
        content, "Add New Product", add_product
    ).pack(anchor="w", pady=8)

    make_button(
        content, "Delete Product by ID", delete_product
    ).pack(anchor="w", pady=8)

    make_button(
        content, "Update Stock by ID", update_stock
    ).pack(anchor="w", pady=8)

    make_button(
        content, "View Product Catalog", show_products
    ).pack(anchor="w", pady=8)

    try:
        rows = fetch_all(
            """
            SELECT
                COUNT(*) AS product_count,
                COALESCE(SUM(stock), 0) AS total_stock
            FROM products
            """
        )

        tk.Label(
            content,
            text=(
                f'Total product types: {rows[0]["product_count"]}\n'
                f'Total units in stock: {rows[0]["total_stock"]}'
            ),
            font=("Arial", 12, "bold"),
            bg="#f1f5f9",
            fg="#12345a",
            justify="left"
        ).pack(anchor="w", pady=20)

    except Error as e:
        messagebox.showerror("Database Error", str(e))


# =====================================================
# 8. ORDER HISTORY
# =====================================================

def show_orders():
    clear_content()
    heading("Order History")

    columns = (
        "Order ID",
        "Customer",
        "Date",
        "Total (Rs.)",
        "Status"
    )

    tree = ttk.Treeview(
        content,
        columns=columns,
        show="headings"
    )

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=175)

    tree.pack(fill="both", expand=True)

    def refresh_orders():
        tree.delete(*tree.get_children())

        try:
            rows = fetch_all(
                """
                SELECT order_id, customer_name, order_date,
                       total_amount, status
                FROM orders
                ORDER BY order_id DESC
                """
            )

            for order in rows:
                tree.insert(
                    "",
                    "end",
                    iid=str(order["order_id"]),
                    values=(
                        order["order_id"],
                        order["customer_name"],
                        str(order["order_date"]),
                        f'{order["total_amount"]:,.2f}',
                        order["status"]
                    )
                )

        except Error as e:
            messagebox.showerror("Database Error", str(e))

    def view_details():
        selected = tree.selection()

        if not selected:
            messagebox.showwarning(
                "Select Order", "Select an order to view its details."
            )
            return

        order_id = int(selected[0])

        try:
            items = fetch_all(
                """
                SELECT product_name, quantity, price
                FROM order_items
                WHERE order_id = %s
                """,
                (order_id,)
            )

            payments = fetch_all(
                """
                SELECT method, payment_status
                FROM payments
                WHERE order_id = %s
                """,
                (order_id,)
            )

            lines = [f"Order ID: {order_id}", "", "Items:"]

            for item in items:
                subtotal = item["price"] * item["quantity"]
                lines.append(
                    f'{item["product_name"]} x {item["quantity"]} '
                    f'= Rs. {subtotal:,.2f}'
                )

            if payments:
                lines.extend([
                    "",
                    f'Payment method: {payments[0]["method"]}',
                    f'Payment status: {payments[0]["payment_status"]}'
                ])

            messagebox.showinfo(
                "Order Details",
                "\n".join(lines)
            )

        except Error as e:
            messagebox.showerror("Database Error", str(e))

    buttons = tk.Frame(content, bg="#f1f5f9")
    buttons.pack(fill="x", pady=10)

    make_button(
        buttons, "Refresh Orders", refresh_orders
    ).pack(side="left")

    make_button(
        buttons, "View Order Details", view_details
    ).pack(side="right")

    refresh_orders()


# =====================================================
# 9. NAVIGATION
# =====================================================

make_button(nav, "Products", show_products).pack(
    side="left", padx=8, pady=8
)

make_button(nav, "Shopping Cart", show_cart).pack(
    side="left", padx=8, pady=8
)

make_button(nav, "Admin", show_admin).pack(
    side="left", padx=8, pady=8
)

make_button(nav, "Order History", show_orders).pack(
    side="left", padx=8, pady=8
)


# =====================================================
# 10. CLOSE APPLICATION CLEANLY
# =====================================================

def close_application():
    try:
        if conn.is_connected():
            conn.close()
    except Error:
        pass

    root.destroy()


root.protocol("WM_DELETE_WINDOW", close_application)

show_products()
root.mainloop()
