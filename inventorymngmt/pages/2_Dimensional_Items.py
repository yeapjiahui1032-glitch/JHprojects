import streamlit as st
from Repo import create_table
from Model import Product
from Repo import get_allproducts, add_product, reduce_product_quantity, increase_product_quantity, delete_product
import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(page_title="Dimensional Items", layout="wide")
st.title("Dimensional Items ")

st.subheader("Add New Product")

with st.form("add_dimensional_form"):
    name = st.text_input("Name")
    quantity = st.number_input("Quantity",min_value=0, step=1)
    min_stock = st.number_input("Minimum Stock",min_value=0, step=1)
    category = st.selectbox("Category", ["Wood", "Metal", "Plastic"])
    location = st.selectbox("Location",["Malaysia","Singapore"])
    length = st.number_input("Length (cm)", min_value=0.0, step=0.1)
    width = st.number_input("Width (cm)", min_value=0.0, step=0.1)

    submitted = st.form_submit_button("Add Product")

    if submitted:
        st.info(f"Adding new product...")
        add_product(Product(name=name, 
                            quantity=quantity, 
                            min_stock=min_stock, 
                            category=category, 
                            location=location,
                            length=length,
                            width=width,
                            sku=None 
                            ))
        if add_product:
            st.success("Product added successfully!")
        else:
            st.error("Failed to add product. Check the details entered.")


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
        "length": p.length,
        "width": p.width,
        "created_at": p.created_at,
        "status": "Low Stock" if p.quantity < p.min_stock else "In Stock"
    }
    for p in products
]
st.dataframe(data, use_container_width=True)