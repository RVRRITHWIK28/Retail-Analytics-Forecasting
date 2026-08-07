import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import plotly.express as px
import pandas as pd

from retail_and_forecasting.forecasting import forecast_sales

from services.dashboard_service import (
    get_kpis,
    get_countries,
    revenue_trend,
    top_products,
    country_sales,
    monthly_sales,
    business_insights,
    world_revenue,
)

# --------------------------
# Page Config
# --------------------------

st.set_page_config(
    page_title="Retail Analytics Platform",
    page_icon="📈",
    layout="wide"
)

# --------------------------
# Header
# --------------------------

st.markdown("""
<h1 style="
    text-align:center;
    color:#2E86DE;
    font-size:42px;
    margin-bottom:0px;
">
📊 Retail Analytics & Demand Forecasting Platform
</h1>

<p style="
    text-align:center;
    color:gray;
    font-size:18px;
    margin-top:0px;
">
Production-Level Business Intelligence Dashboard
</p>
""", unsafe_allow_html=True)

st.markdown("""
<style>

/* Selectbox */
div[data-baseweb="select"]{
    border-radius:10px;
    transition:0.3s;
    cursor:pointer !important;
}

div[data-baseweb="select"]:hover{
    border:1px solid #4F8BF9;
    box-shadow:0 0 10px rgba(79,139,249,0.35);
}

div[data-baseweb="select"] *{
    cursor:pointer !important;
}

</style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([4,2,1])

with col3:
    st.caption("🕒 " + datetime.now().strftime("%d-%b-%Y %I:%M %p"))

st.divider()


# --------------------------
# Sidebar
# --------------------------

st.sidebar.markdown("""
# 🌍 FILTER PANEL
---
""")

countries = get_countries()

selected_country = st.sidebar.selectbox(
    "📍 Select Country",
    ["All"] + countries,
    help="Choose a country to update the dashboard."
)

with st.spinner("Loading Dashboard..."):

    revenue, orders, customers, country_count = get_kpis(selected_country)

st.sidebar.markdown("---")

st.sidebar.markdown("### 📊 Quick Statistics")

st.sidebar.metric(
    "💰 Revenue",
    f"₹{revenue/1000000:.2f} M"
)

st.sidebar.metric(
    "📦 Orders",
    f"{orders:,}"
)

st.sidebar.metric(
    "👥 Customers",
    f"{customers:,}"
)

st.sidebar.markdown("---")

st.sidebar.markdown("### 📥 Export Data")

monthly_df = monthly_sales(selected_country)

csv = monthly_df.to_csv(index=False).encode("utf-8")

st.sidebar.download_button(
    label="⬇️ Download CSV",
    data=csv,
    file_name="monthly_sales.csv",
    mime="text/csv",
    use_container_width=True
)

st.sidebar.markdown("---")

st.sidebar.markdown("### ℹ️ Dashboard Information")

st.sidebar.success("🟢 PostgreSQL Connected")

st.sidebar.write("**Version:** 1.0")

st.sidebar.write("**Status:** Production")

st.sidebar.caption("Retail Analytics Platform")


# --------------------------------------------------
# KPI CARDS
# --------------------------------------------------

c1, c2, c3, c4 = st.columns(4)

cards = [
    ("💰", "Revenue", f"₹{revenue/1000000:.2f} M", "#16A34A"),
    ("📦", "Orders", f"{orders:,}", "#2563EB"),
    ("👥", "Customers", f"{customers:,}", "#9333EA"),
    ("🌍", "Countries", f"{country_count}", "#EA580C")
]

for col, (icon, title, value, color) in zip([c1, c2, c3, c4], cards):

    with col:

        st.markdown(f"""
        <div style="
            background:white;
            border-radius:16px;
            padding:20px;
            border-top:5px solid {color};
            box-shadow:0px 4px 12px rgba(0,0,0,0.12);
        ">

        <div style="font-size:32px;">
            {icon}
        </div>

        <div style="
            font-size:16px;
            color:#666;
            font-weight:600;
            margin-top:8px;
        ">
            {title}
        </div>

        <div style="
            font-size:30px;
            color:{color};
            font-weight:bold;
            margin-top:14px;
        ">
            {value}
        </div>

        </div>
        """, unsafe_allow_html=True)

st.divider()

# --------------------------
# Revenue Trend
# --------------------------

st.markdown(
    """
    <h2 style='text-align:center;'>
        📈 Monthly Revenue Trend
    </h2>
    """,
    unsafe_allow_html=True
)

trend = revenue_trend(selected_country)

# Year + Month ni oka label ga create chestham
trend["Period"] = trend["month"].astype(str) + "-" + trend["year"].astype(str)

fig = px.line(
    trend,
    x="Period",
    y="revenue",
    markers=True,
    color_discrete_sequence=["#2563EB"],
    title=f"Revenue Trend - {selected_country}"
)

fig.update_layout(
    template="plotly_white",
    height=500,
    xaxis_title="Month",
    yaxis_title="Revenue"
)
fig.update_traces(
hovertemplate="<b>%{x}</b><br>Revenue: ₹%{y:,.2f}<extra></extra>"
)


st.plotly_chart(fig, use_container_width=True)

st.divider()

left, right = st.columns(2)

# -----------------------------------
# Top Products
# -----------------------------------

with left:

    st.subheader("🏆 Top Products")

    products = top_products(selected_country)

    fig = px.bar(
        products,
        x="revenue",
        y="description",
        orientation="h",
        color_discrete_sequence=["#16A34A"],
        title="Top 10 Products"
    )

    fig.update_layout(
        template="plotly_white",
        height=450,
        yaxis={"categoryorder": "total ascending"}
    )
    fig.update_traces(
    hovertemplate="<b>%{x}</b><br>Revenue: ₹%{y:,.2f}<extra></extra>"
    )

    st.plotly_chart(fig, use_container_width=True)

# -----------------------------------
# Country Revenue
# -----------------------------------

with right:

    st.subheader("🌍 Country Revenue")

    country_df = country_sales(selected_country)

    fig = px.bar(
        country_df,
        x="country",
        y="revenue",
        color_discrete_sequence=["#F97316"],
        title="Revenue by Country"
    )

    fig.update_layout(
        template="plotly_white",
        height=450
    )
    fig.update_traces(
    hovertemplate="<b>%{x}</b><br>Revenue: ₹%{y:,.2f}<extra></extra>"
    )

    st.plotly_chart(fig, use_container_width=True)

st.divider()

left, right = st.columns(2)

# -----------------------------------
# Monthly Sales
# -----------------------------------

with left:

    st.subheader("📅 Monthly Sales")

    monthly_df = monthly_sales(selected_country)

    monthly_df["Period"] = (
        monthly_df["month"].astype(str)
        + "-"
        + monthly_df["year"].astype(str)
    )

    fig = px.bar(
        monthly_df,
        x="Period",
        y="revenue",
        color_discrete_sequence=["#9333EA"],
        title="Monthly Revenue"
    )

    fig.update_layout(
        template="plotly_white",
        height=450
    )
    fig.update_traces(
    hovertemplate="<b>%{x}</b><br>Revenue: ₹%{y:,.2f}<extra></extra>"
    )

    st.plotly_chart(fig, use_container_width=True)

# -----------------------------------
# Forecast
# -----------------------------------

with right:

    st.subheader("🔮 Demand Forecast")

    forecast_df = forecast_sales(monthly_df)

    history = monthly_df.copy()

    history = history.rename(columns={"revenue":"Sales"})

    history["Type"] = "Historical"

    forecast_chart = forecast_df.reset_index()

    forecast_chart.columns = ["Period","Sales"]

    forecast_chart["Type"] = "Forecast"

    combined = pd.concat([
        history[["Period","Sales","Type"]],
        forecast_chart
    ])

    fig = px.line(
        combined,
        x="Period",
        y="Sales",
        color="Type",
        markers=True,
        color_discrete_sequence=["#DC2626","#2563EB"],
        title="Next 3 Months Forecast"
    )

    fig.update_layout(
        template="plotly_white",
        height=450
    )
    fig.update_traces(
    hovertemplate="<b>%{x}</b><br>Revenue: ₹%{y:,.2f}<extra></extra>"
    )

    st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("🤖 AI Business Insights")

insights = business_insights(selected_country)

revenue = insights.iloc[0]["revenue"]
avg_order = insights.iloc[0]["avg_order"]
max_sale = insights.iloc[0]["max_sale"]

c1, c2, c3 = st.columns(3)

cards = [
    ("💰", "Total Revenue", f"₹{revenue:,.2f}", "#16A34A"),
    ("📦", "Average Order", f"₹{avg_order:,.2f}", "#2563EB"),
    ("🚀", "Highest Sale", f"₹{max_sale:,.2f}", "#EA580C")
]

for col, (icon, title, value, color) in zip([c1, c2, c3], cards):

    with col:

        st.markdown(f"""
        <div style="
            background:white;
            border-radius:15px;
            padding:18px;
            border-left:6px solid {color};
            box-shadow:0px 4px 12px rgba(0,0,0,0.12);
        ">

        <div style="font-size:28px;">
            {icon}
        </div>

        <div style="
            color:#666;
            font-size:15px;
            font-weight:600;
            margin-top:8px;
        ">
            {title}
        </div>

        <div style="
            color:{color};
            font-size:28px;
            font-weight:bold;
            margin-top:12px;
        ">
            {value}
        </div>

        </div>
        """, unsafe_allow_html=True)

country_df = country_sales(selected_country)

if selected_country == "All":
    top_market = country_df.iloc[0]["country"]
else:
    top_market = selected_country

st.divider()

st.subheader("📋 Executive Summary")
country_df = country_sales(selected_country)

if selected_country == "All":
    top_market = country_df.iloc[0]["country"]
else:
    top_market = selected_country

st.markdown(f"""
<div style="
    background:#ffffff;
    padding:25px;
    border-radius:15px;
    border-left:8px solid #2563EB;
    box-shadow:0px 4px 12px rgba(0,0,0,0.10);
    color:#000000;
">
<p style="font-size:17px; color:black;">
💰 <b>Total Revenue:</b> ₹{revenue:,.2f}
</p>

<p style="font-size:17px; color:black;">
📦 <b>Total Orders:</b> {orders:,}
</p>

<p style="font-size:17px; color:black;">
👥 <b>Total Customers:</b> {customers:,}
</p>

<p style="font-size:17px; color:black;">
🌍 <b>Selected Country:</b> {selected_country}
</p>

<p style="font-size:17px; color:black;">
🏆 <b>Top Market:</b> {top_market}
</p>

<p style="font-size:17px; color:black;">
🔮 <b>Forecast Status:</b> Next 3 Months Generated Successfully
</p>

<p style="font-size:17px; color:black;">
🤖 <b>AI Insights:</b> Updated Successfully
</p>

</div>
""", unsafe_allow_html=True)

st.divider()

st.markdown("""
<div style="
    text-align:center;
    color:#9CA3AF;
    font-size:15px;
    padding:15px;
">

🚀 Built with <b>Python</b> • <b>Streamlit</b> • <b>PostgreSQL</b> • <b>Plotly</b>

© 2026 Retail Analytics & Demand Forecasting Platform

</div>
""", unsafe_allow_html=True)

st.divider()

st.markdown("## 🌍 Global Revenue Distribution")

world_df = world_revenue()

fig = px.choropleth(
    world_df,
    locations="country",
    locationmode="country names",
    color="revenue",
    hover_name="country",
    color_continuous_scale="Blues",
    title="Revenue by Country"
)

fig.update_layout(
    template="plotly_white",
    height=600,
    title_x=0.5,
    margin=dict(l=0, r=0, t=60, b=0)
)

st.plotly_chart(fig, use_container_width=True)