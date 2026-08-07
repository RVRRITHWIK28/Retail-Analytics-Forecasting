import streamlit as st

def kpi_card(title, value, icon):

    st.markdown(
        f"""
        <div style="
            background:#1e293b;
            padding:20px;
            border-radius:15px;
            box-shadow:0 5px 10px rgba(0,0,0,0.25);
            text-align:center;
        ">
            <h3>{icon} {title}</h3>
            <h1 style="color:#00E5FF;">{value}</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )
