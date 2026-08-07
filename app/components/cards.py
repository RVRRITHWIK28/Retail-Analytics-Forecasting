import streamlit as st

def kpi_card(title, value):
    st.metric(title, value)