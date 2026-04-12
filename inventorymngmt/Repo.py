import sqlite3
from Model import Product




db_connection = sqlite3.connect('products.db')
db_cursor = db_connection.cursor()
def create_table():
    db_cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sku TEXT NOT NULL UNIQUE,
            quantity INTEGER NOT NULL,
            min_stock INTEGER NOT NULL,
            category TEXT NOT NULL,
            location TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')

def get_allproducts():
    db_cursor.execute('SELECT * FROM products')
    all_products = db_cursor.fetchall()
    products = []
    for row in all_products:
        product = Product(
            id=row[0],
            name=row[1],
            sku=row[2],
            quantity=row[3],
            min_stock=row[4],
            category=row[5],
            location=row[6],
            created_at=row[7],
            updated_at=row[8]
        )
        products.append(product)
    return products

def add_product(product):
    db_cursor.execute("SELECT * FROM products WHERE sku = ?", (product.sku,))
    results = db_cursor.fetchone()
    if results:
        print("Product with this SKU already exists.")
        return False
    else:
        with db_connection:
            db_cursor.execute('''
                INSERT INTO products (name, sku, quantity, min_stock, category, location, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                product.name,
                product.sku,
                product.quantity,
                product.min_stock,
                product.category,
                product.location,
                product.created_at,
                product.updated_at,
            ))
        print("Product added successfully.")
        return True

def reduce_product_quantity(id: int, quantity: int):
    db_cursor.execute("SELECT * FROM products WHERE id=:id", {'id': id})
    stock = db_cursor.fetchone()
    if not stock:
        print("No such product!")
        return
    else:
        new_product_quantity = stock[3] - quantity
        if new_product_quantity < 0:
            print('Not enough products in stock to reduce by that quantity!')
            return
        else:
            with db_connection:
                db_cursor.execute(
                    "UPDATE products SET quantity=:quantity WHERE id=:id",
                    {'id': id, 'quantity': new_product_quantity}
                )

def increase_product_quantity(id: int, quantity: int):
    db_cursor.execute("SELECT * FROM products WHERE id=:id", {'id': id})
    stock = db_cursor.fetchone()
    if not stock:
        print("No such product!")
        return
    else:
        new_stock_quantity = stock[3] + quantity
        with db_connection:
            db_cursor.execute(
                "UPDATE products SET quantity=:quantity WHERE id=:id",
                {'id': id, 'quantity': new_stock_quantity}
            )

def delete_product(id):
    with db_connection:
        db_cursor .execute("DELETE from products WHERE id=:id", {'id': id})