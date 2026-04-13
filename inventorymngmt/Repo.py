import os
import sqlite3
from Model import Product
import streamlit as st
import uuid
import random
import string

def generate_sku(length=8):
    """Generate a random SKU consisting of uppercase letters and digits."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

DB_PATH = os.path.join(os.path.dirname(__file__), 'products.db')
@st.cache_resource
def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False) 
    return conn

def get_cursor():
    conn = get_db_connection()
    return conn,conn.cursor()

def create_table():
    conn, cur = get_cursor()
    cur.execute('''
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
    conn.commit()

def get_allproducts():
    conn, cur = get_cursor()
    cur.execute('SELECT * FROM products')
    all_products = cur.fetchall()
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
    conn, cur = get_cursor()
    if not product.sku:
        product.sku = generate_sku()
    cur.execute("SELECT * FROM products WHERE sku = ?", (product.sku,))
    results = cur.fetchone()
    if results:
        print("Product with this SKU already exists.")
        return False
    else:
        with conn:
            cur.execute('''
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
            conn.commit()
        print("Product added successfully.")
        return True

def reduce_product_quantity(sku: str, quantity: int):
    conn, cur = get_cursor()
    cur.execute("SELECT * FROM products WHERE sku=:sku", {'sku': sku})
    stock = cur.fetchone()
    if not stock:
        print("No such product!")
        return
    else:
        new_product_quantity = stock[3] - quantity
        if new_product_quantity < 0:
            print('Not enough products in stock to reduce by that quantity!')
            return
        else:
            with conn:
                cur.execute(
                    "UPDATE products SET quantity=:quantity WHERE sku=:sku",
                    {'sku': sku, 'quantity': new_product_quantity}
                )
                conn.commit()

def increase_product_quantity(sku: str, quantity: int):
    conn, cur = get_cursor()
    cur.execute("SELECT * FROM products WHERE sku=:sku", {'sku': sku})
    stock = cur.fetchone()
    if not stock:
        print("No such product!")
        return
    else:
        new_stock_quantity = stock[3] + quantity
        with conn:
            cur.execute(
                "UPDATE products SET quantity=:quantity WHERE sku=:sku",
                {'sku': sku, 'quantity': new_stock_quantity}
            )
            conn.commit()

def delete_product(sku: str):
    conn, cur = get_cursor()
    with conn:
        cur.execute("DELETE from products WHERE sku=:sku", {'sku': sku})