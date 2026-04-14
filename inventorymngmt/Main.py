
import streamlit as st
from Repo import create_table
from Model import Product
from Repo import get_allproducts, add_product, reduce_product_quantity, increase_product_quantity, delete_product

st.set_page_config(page_title="Inventory Management System", layout="wide")
st.title("Inventory Management System :warehouse:")

if st.button(" Go to Dimensional Items"):
    st.switch_page("pages/2_Dimensional_Items.py")

if st.button("Initialize Database", help="Initialize the database"):
    create_table()
    st.success("Database initialized successfully!")

st.subheader("Add New Product")

with st.form("add_product_form"):
    name = st.text_input("Name")
    quantity = st.number_input("Quantity",min_value=0, step=1)
    min_stock = st.number_input("Minimum Stock",min_value=0, step=1)
    category = st.selectbox("Category", ["Wood", "Metal", "Plastic"])
    location = st.selectbox("Location",["Malaysia","Singapore"])
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
        reduce_id = st.text_input("Product SKU to Reduce")
        reduce_quantity = st.number_input("Quantity to Reduce", min_value=0, step=1)
        reduce_submitted = st.form_submit_button("Reduce Quantity")
        if reduce_submitted:
            result = reduce_product_quantity(reduce_id, reduce_quantity)
            if result is True:
                st.success("Quantity reduced successfully!")
            else:
                st.error("Failed! Check the SKU or quantity entered.")
with col2:
    with st.form("increase_quantity_form"):
        increase_id = st.text_input("Product SKU to Increase")
        increase_quantity = st.number_input("Quantity to Increase", min_value=0, step=1)
        increase_submitted = st.form_submit_button("Increase Quantity")

        if increase_submitted:
            result = increase_product_quantity(increase_id, increase_quantity)
            if result:
                st.success("Quantity increased successfully!")
            else:
                 st.error("Failed! Check the SKU or quantity entered.")


st.subheader("Delete Product")
delete_id = st.text_input("Product SKU to Delete")
if st.button("Delete Product"):
    st.info(f"Deleting product...")
    delete_product(delete_id)
    st.success("Product deleted successfully!")
else:
        st.error("Failed! Check the SKU entered.")

if __name__ == "__main__":
    st.write("Welcome to the Inventory Management System! Use the sidebar to manage your inventory.")