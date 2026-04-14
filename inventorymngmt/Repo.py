import os
import random
import string
import streamlit as st
from supabase import create_client
from Model import Product

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

def generate_sku(length=8):
    """Generate a random SKU consisting of uppercase letters and digits."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@st.cache_resource
def get_db_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)



def get_allproducts():
    conn = get_db_connection()
    response = conn.table("products").select("*").execute()
    all_products = response.data
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
    conn = get_db_connection()
    if not product.sku:
        product.sku = generate_sku()
    response = conn.table("products").select("*").eq("sku", product.sku).execute()
    results = response.data
    if results:
        print("Product with this SKU already exists.")
        return False
    conn.table("products").insert({
                "name": product.name,
                "sku": product.sku,
                "length": product.length,
                "width": product.width,
                "quantity": product.quantity,
                "min_stock": product.min_stock,
                "category": product.category,
                "location": product.location,
                "created_at": product.created_at,
                "updated_at": product.updated_at
            }).execute()
    return True

def reduce_product_quantity(sku: str, quantity: int):
    conn = get_db_connection()
    response = conn.table("products").select("*").eq("sku", sku).execute()
    stock = response.data
    if not stock:
        print("No such product!")
        return False          # ← explicit False
    else:
        new_product_quantity = stock - quantity
        if new_product_quantity < 0:
            print('Not enough products in stock!')
            return False      # ← explicit False
        conn.table("products").update({"quantity": new_product_quantity}).eq("sku", sku).execute()
        return True      

def increase_product_quantity(sku: str, quantity: int):
    conn = get_db_connection()
    response = conn.table("products").select("*").eq("sku", sku).execute()
    stock = response.data
    if not stock:
        print("No such product!")
        return False
    if quantity < 0:
        print("Quantity to increase must be positive!")
        return False
    else:
        new_stock_quantity = stock + quantity
        conn.table("products").update({"quantity": new_stock_quantity}).eq("sku", sku).execute()
        return True
    
def reduce_dimension(sku: str, length: float, width: float):
    conn = get_db_connection()
    response = conn.table("products").select("*").eq("sku", sku).execute()
    stock = response.data
    if not stock:
        print("No such product!")
        return False
    else:
        new_length = stock[3] - length
        new_width = stock[4] - width
        if new_length < 0 or new_width < 0:
            print('Dimension cannot go below zero!')
            return False
        conn.table("products").update({"length": new_length, "width": new_width}).eq("sku", sku).execute()
        return True

def increase_dimension(sku: str, length: float, width: float):
    conn = get_db_connection()
    response = conn.table("products").select("*").eq("sku", sku).execute()
    stock = response.data
    if not stock:
        print("No such product!")
        return False
    else:
        new_length = stock[3] + length
        new_width = stock[4] + width
        conn.table("products").update({"length": new_length, "width": new_width}).eq("sku", sku).execute()
        return True



def delete_product(sku: str):
    conn = get_db_connection()
    conn.table("products").delete().eq("sku", sku).execute()
    return True