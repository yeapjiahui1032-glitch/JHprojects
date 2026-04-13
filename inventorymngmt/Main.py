
import streamlit as st
from Repo import create_table
from Model import Product
from Repo import get_allproducts, add_product, reduce_product_quantity, increase_product_quantity, delete_product

st.set_page_config(page_title="Inventory Management System", layout="wide")
st.title("Inventory Management System :warehouse:")


if st.button("Initialize Database", help="Initialize the database"):
    create_table()
    st.success("Database initialized successfully!")

st.subheader("Add New Product")

with st.form("add_product_form"):
    name = st.text_input("Name")
    quantity = st.number_input("Quantity",min_value=0, step=1)
    min_stock = st.number_input("Minimum Stock",min_value=0, step=1)
    category = st.text_input("Category")
    location = st.text_input("Location")
    submitted = st.form_submit_button("Add Product")

    if submitted:
        st.info(f"Adding new product...")
        add_product(Product(name=name, 
                            quantity=quantity, 
                            min_stock=min_stock, 
                            category=category, 
                            location=location,
                            sku=None 
                            ))
        st.success("Product added successfully!")

st.subheader(" Inventory")
products = get_allproducts()
data =[
    {
        "Name": p.name,
        "SKU": p.sku,
        "Quantity": p.quantity,
        "Min Stock": p.min_stock,
        "Category": p.category,
        "Location": p.location,
        "created_at": p.created_at,
        "status": "Low Stock" if p.quantity < p.min_stock else "In Stock"
    }
    for p in products
]
st.dataframe(data, use_container_width=True)
st.subheader("Update Product Quantity")
col1, col2 = st.columns(2)
with col1:
    with st.form("reduce_quantity_form"):
        reduce_id = st.text_input("Product SKU to Reduce", step=1)
        reduce_quantity = st.number_input("Quantity to Reduce", min_value=0, step=1)
        reduce_submitted = st.form_submit_button("Reduce Quantity")

        if reduce_submitted:
            st.info(f"Reducing stock quantity...")
            reduce_product_quantity(reduce_id, reduce_quantity)
            st.success("Product quantity updated successfully!")
with col2:
    with st.form("increase_quantity_form"):
        increase_id = st.text_input("Product SKU to Increase", step=1)
        increase_quantity = st.number_input("Quantity to Increase", min_value=0, step=1)
        increase_submitted = st.form_submit_button("Increase Quantity")

        if increase_submitted:
            st.info(f"Increasing stock quantity...")
            increase_product_quantity(increase_id, increase_quantity)
            st.success("Product quantity updated successfully!")
st.subheader("Delete Product")
delete_id = st.text_input("Product SKU to Delete", step=1)
if st.button("Delete Product"):
    st.info(f"Deleting product...")
    delete_product(delete_id)
    st.success("Product deleted successfully!")

if __name__ == "__main__":
    st.write("Welcome to the Inventory Management System! Use the sidebar to manage your inventory.")