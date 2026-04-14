import os
from urllib import response
from supabase import create_client
from Model import Product
import streamlit as st
import uuid
import random
import string

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

def generate_sku(length=8):
    """Generate a random SKU consisting of uppercase letters and digits."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@st.cache_resource
def get_db_connection():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

def get_cursor():
    conn = get_db_connection()
    response = conn.table("products").select("*").execute()
    products = response.data
    return conn,conn.cursor()

def create_table():
    conn, cur = get_cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sku TEXT NOT NULL UNIQUE,
            length REAL,
            width REAL,     
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
            length=row[3],
            width=row[4],
            quantity=row[5],
            min_stock=row[6],
            category=row[7],
            location=row[8],
            created_at=row[9],
            updated_at=row[10]
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
                INSERT INTO products (name, sku,length, width, quantity, min_stock, category, location, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                product.name,
                product.sku,
                product.length,
                product.width,
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
        return False          # ← explicit False
    else:
        new_product_quantity = stock[5] - quantity
        if new_product_quantity < 0:
            print('Not enough products in stock!')
            return False      # ← explicit False
        else:
            with conn:
                cur.execute(
                    "UPDATE products SET quantity=:quantity WHERE sku=:sku",
                    {'sku': sku, 'quantity': new_product_quantity}
                )
                conn.commit()
            return True      

def increase_product_quantity(sku: str, quantity: int):
    conn, cur = get_cursor()
    cur.execute("SELECT * FROM products WHERE sku=:sku", {'sku': sku})
    stock = cur.fetchone()
    if not stock:
        print("No such product!")
        return False
    if quantity < 0:
        print("Quantity to increase must be positive!")
        return False
    else:
        new_stock_quantity = stock[5] + quantity
        with conn:
            cur.execute(
                "UPDATE products SET quantity=:quantity WHERE sku=:sku",
                {'sku': sku, 'quantity': new_stock_quantity}
            )
            conn.commit()
        return True
    
def reduce_dimension(sku: str, length: float, width: float):
    conn, cur = get_cursor()
    cur.execute("SELECT * FROM products WHERE sku=:sku", {'sku': sku})
    stock = cur.fetchone()
    if not stock:
        print("No such product!")
        return False
    else:
        new_length = stock[3] - length
        new_width = stock[4] - width
        if new_length < 0 or new_width < 0:
            print('Dimension cannot go below zero!')
            return False
        else:
            with conn:
                cur.execute(
                    "UPDATE products SET length=:length, width=:width WHERE sku=:sku",
                    {'sku': sku, 'length': new_length, 'width': new_width}  # ← correct columns
                )
                conn.commit()
            return True

def increase_dimension(sku: str, length: float, width: float):
    conn, cur = get_cursor()
    cur.execute("SELECT * FROM products WHERE sku=:sku", {'sku': sku})
    stock = cur.fetchone()
    if not stock:
        print("No such product!")
        return False
    else:
        new_length = stock[3] + length
        new_width = stock[4] + width
        with conn:
            cur.execute(
                "UPDATE products SET length=:length, width=:width WHERE sku=:sku",
                {'sku': sku, 'length': new_length, 'width': new_width}  # ← correct columns
            )
            conn.commit()
        return True



def delete_product(sku: str):
    conn, cur = get_cursor()
    with conn:
        cur.execute("DELETE from products WHERE sku=:sku", {'sku': sku})
        conn.commit()
        return True