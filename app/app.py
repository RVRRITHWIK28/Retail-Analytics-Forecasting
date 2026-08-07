import streamlit as st

st.set_page_config(
    page_title="Retail Analytics Platform",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Retail Analytics Platform")

st.markdown("---")

from components.cards import kpi_card

col1, col2, col3, col4 = st.columns(4)

with col1:
    kpi_card("Revenue", "₹8.91M")

with col2:
    kpi_card("Orders", "18,523")

with col3:
    kpi_card("Customers", "4,372")

with col4:
    kpi_card("Countries", "38")