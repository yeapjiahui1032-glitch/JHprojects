import streamlit as st
from Repo import create_table
from Model import Product
from Repo import get_allproducts, add_product, reduce_product_quantity, increase_product_quantity, delete_product
import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(page_title="Dimensional Items", layout="wide")
st.title("Dimensional Items ")

if st.button(" Back to Main"):
    st.switch_page("Main.py")

st.subheader("Add New Product")

with st.form("add_dimensional_form"):
    name = st.text_input("Name")
    quantity = st.number_input("Quantity",min_value=0, step=1)
    min_stock = st.number_input("Minimum Stock",min_value=0, step=1)
    category = st.selectbox("Category", ["Wood", "Metal", "Plastic"])
    location = st.selectbox("Location",["Malaysia","Singapore"])
    length = st.number_input("Length (m)", min_value=0.0, step=0.1)
    width = st.number_input("Width (m)", min_value=0.0, step=0.1)

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

st.dataframe(data, use_container_width=True)
st.subheader("Update Product Quantity")
col1, col2 = st.columns(2)
with col1:
    with st.form("reduce_quantity_form"):
        d_reduce_id = st.text_input("Product SKU to Reduce")
        d_reduce_quantity = st.number_input("Quantity to Reduce", min_value=0, step=1)
        d_reduce_submitted = st.form_submit_button("Reduce Quantity")
        if d_reduce_submitted:
            result = reduce_product_quantity(d_reduce_id, d_reduce_quantity)
            if result is True:
                st.success("Quantity reduced successfully!")
            else:
                st.error("Failed! Check the SKU or quantity entered.")
with col2:
    with st.form("increase_quantity_form"):
        d_increase_id = st.text_input("Product SKU to Increase")
        d_increase_quantity = st.number_input("Quantity to Increase", min_value=0, step=1)
        d_increase_submitted = st.form_submit_button("Increase Quantity")

        if d_increase_submitted:
            result = d_increase_quantity(d_increase_id, d_increase_quantity)
            if result:
                st.success("Quantity increased successfully!")
            else:
                 st.error("Failed! Check the SKU or quantity entered.")

st.subheader("Update Product Dimensions")
col1, col2 = st.columns(2)
with col1:
    with st.form("reduce length"):
        d_reduce_dimension_id = st.text_input("Product SKU to Reduce")
        d_reduce_dimension_quantity = st.number_input("Quantity to Reduce", min_value=0, step=0.1)
        d_reduce_dimension_sumbmitted = st.form_submit_button("Reduce Length")

    if d_increase_submitted:
            result = d_reduce_dimension_quantity(d_reduce_dimension_id , d_reduce_dimension_quantity)
            if result:
                st.success("Quantity reduced successfully!")
            else:
                 st.error("Failed! Check the SKU or quantity entered.")

with col2:
    with st.form("increase length"):
        d_increase_dimension_id = st.text_input("Product SKU to Increase")
        d_increase_dimension_quantity = st.number_input("Quantity to Increase", min_value=0, step=0.1)
        d_increase_dimension_sumbmitted = st.form_submit_button("Increase Length")

    if d_increase_submitted:
            result = d_reduce_dimension_quantity(d_reduce_dimension_id , d_reduce_dimension_quantity)
            if result:
                st.success("Quantity increased successfully!")
            else:
                 st.error("Failed! Check the SKU or quantity entered.")


st.subheader("Delete Product")
with st.form("Delete Product"):
    delete_id = st.text_input("Product SKU to Delete")
    delete_submitted = st.form_submit_button("Delete Product")
    if delete_submitted:
        result = delete_product(delete_id)
        if result:
            st.success("Product deleted sucessfully")
        else:
            st.error("Failed! Check the SKU")