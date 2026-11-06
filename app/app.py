import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import plotly.express as px
import pandas as pd

from services.snowflake_dashboard_service import (
    get_countries,
    get_kpis,
    get_model_comparison,
    get_future_forecasts,
    revenue_trend,
    top_products,
    country_sales,
    monthly_sales,
    business_insights,
    world_revenue
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
# Header & Styling
# --------------------------
st.markdown("""
<h1 style="text-align:center; color:#2E86DE; font-size:42px; margin-bottom:0px;">
📊 Retail Analytics & Demand Forecasting Platform
</h1>
<p style="text-align:center; color:gray; font-size:18px; margin-top:0px;">
Production-Level Business Intelligence Dashboard
</p>
<style>
section[data-testid="stSidebar"] { width: 230px !important; min-width: 230px !important; }
section[data-testid="stSidebar"] > div { padding-top: 1rem !important; padding-bottom: 0.5rem !important; }
section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label { font-size: 13px !important; }
section[data-testid="stSidebar"] h1 { font-size: 20px !important; margin-bottom: 8px !important; }
div[data-baseweb="select"] { border-radius:10px; transition:0.3s; cursor:pointer !important; min-height: 36px !important; font-size: 13px !important; }
div[data-baseweb="select"]:hover { border:1px solid #4F8BF9; box-shadow:0 0 10px rgba(79,139,249,0.35); }
section[data-testid="stSidebar"] * { cursor: pointer !important; }
</style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([4, 2, 1])
with col3:
    st.markdown(
        f"""
        <div style="
            text-align:right;
            color:#888;
            font-size:11px;
            line-height:1.2;
            margin-top:8px;
        ">
            🕒 {datetime.now().strftime("%d-%b-%Y %I:%M %p")}
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()

# --------------------------
# Sidebar & Initial Load
# --------------------------
st.sidebar.markdown("# 🌍 FILTER PANEL")

countries = get_countries()
selected_country = st.sidebar.selectbox(
    "📍 Select Country",
    ["All"] + countries,
    help="Choose a country to update the dashboard."
)

# Single-fetch patterns to prevent duplicate DB hits
with st.spinner("Fetching Data..."):
    revenue, orders, customers, country_count = get_kpis(selected_country)
    monthly_df = monthly_sales(selected_country)
    country_df = country_sales(selected_country)

st.sidebar.markdown("### 📊 Quick Statistics")
st.sidebar.metric("💰 Revenue", f"₹{revenue/1_000_000:.2f} M")
st.sidebar.metric("📦 Orders", f"{orders:,}")
st.sidebar.metric("👥 Customers", f"{customers:,}")

st.sidebar.markdown("### 📥 Export Monthly Sales Data")
csv = monthly_df.to_csv(index=False).encode("utf-8")
st.sidebar.download_button(
    label="⬇️ Download CSV",
    data=csv,
    file_name="monthly_sales.csv",
    mime="text/csv",
    use_container_width=True
)

st.sidebar.markdown("### ℹ️ Dashboard Info")
st.sidebar.success("🟢 Snowflake Connected")
st.sidebar.write("**Version:** 2.0")
st.sidebar.write("**Status:** Production")
st.sidebar.caption(
    "PySpark → Snowflake → SARIMA + LSTM"
)


# --------------------------------------------------
# KPI CARDS
# --------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
cards = [
    ("💰", "Revenue", f"₹{revenue/1_000_000:.2f} M", "#16A34A"),
    ("📦", "Orders", f"{orders:,}", "#2563EB"),
    ("👥", "Customers", f"{customers:,}", "#9333EA"),
    ("🌍", "Countries", f"{country_count}", "#EA580C")
]

for col, (icon, title, value, color) in zip([c1, c2, c3, c4], cards):
    with col:
        st.markdown(f"""
        <div style="background:white; border-radius:16px; padding:20px; border-top:5px solid {color}; box-shadow:0px 4px 12px rgba(0,0,0,0.12);">
            <div style="font-size:32px;">{icon}</div>
            <div style="font-size:16px; color:#666; font-weight:600; margin-top:8px;">{title}</div>
            <div style="font-size:30px; color:{color}; font-weight:bold; margin-top:14px;">{value}</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# --------------------------
# Revenue Trend
# --------------------------
st.markdown("<h2 style='text-align:center;'>📈 Monthly Revenue Trend</h2>", unsafe_allow_html=True)
trend = revenue_trend(selected_country)

# Proper Date Construction for Chronological Plotly Sorting
trend["Date"] = pd.to_datetime(trend["year"].astype(str) + "-" + trend["month"].astype(str) + "-01")
trend = trend.sort_values("Date")
trend["Period"] = trend["Date"].dt.strftime("%b %Y")

fig_trend = px.line(
    trend,
    x="Period",
    y="revenue",
    markers=True,
    color_discrete_sequence=["#2563EB"],
    title=f"Revenue Trend - {selected_country}"
)
fig_trend.update_layout(template="plotly_white", height=500, xaxis_title="Month", yaxis_title="Revenue")
fig_trend.update_traces(hovertemplate="<b>%{x}</b><br>Revenue: ₹%{y:,.2f}<extra></extra>")
st.plotly_chart(fig_trend, use_container_width=True)

st.divider()

# -----------------------------------
# Top Products & Country Revenue
# -----------------------------------
left, right = st.columns(2)

with left:
    st.subheader("🏆 Top Products")
    products = top_products(selected_country)
    fig_prod = px.bar(
        products,
        x="revenue",
        y="description",
        orientation="h",
        color_discrete_sequence=["#16A34A"],
        title="Top 10 Products"
    )
    fig_prod.update_layout(template="plotly_white", height=450, yaxis={"categoryorder": "total ascending"})
    fig_prod.update_traces(hovertemplate="<b>%{y}</b><br>Revenue: ₹%{x:,.2f}<extra></extra>")
    st.plotly_chart(fig_prod, use_container_width=True)

with right:
    st.subheader("🌍 Country Revenue")
    fig_country = px.bar(
        country_df,
        x="country",
        y="revenue",
        color_discrete_sequence=["#F97316"],
        title="Revenue by Country"
    )
    fig_country.update_layout(template="plotly_white", height=450)
    fig_country.update_traces(hovertemplate="<b>%{x}</b><br>Revenue: ₹%{y:,.2f}<extra></extra>")
    st.plotly_chart(fig_country, use_container_width=True)

st.divider()

# -----------------------------------
# Monthly Sales
# -----------------------------------


st.subheader("📅 Monthly Sales")

monthly_df["Date"] = pd.to_datetime(
    monthly_df["year"].astype(str)
    + "-"
    + monthly_df["month"].astype(str)
    + "-01"
)

monthly_df = monthly_df.sort_values("Date")

monthly_df["Period"] = monthly_df["Date"].dt.strftime("%b %Y")

fig_monthly = px.bar(
    monthly_df,
    x="Period",
    y="revenue",
    color_discrete_sequence=["#9333EA"],
    title="Monthly Revenue"
)

fig_monthly.update_layout(
    template="plotly_white",
    height=450
)

fig_monthly.update_traces(
    hovertemplate="<b>%{x}</b><br>Revenue: ₹%{y:,.2f}<extra></extra>"
)

st.plotly_chart(
    fig_monthly,
    use_container_width=True
)


# ===================================
# Demand Forecast
# ===================================

st.divider()

st.subheader("🔮 Demand Forecast & What-If Scenario Simulator")

growth_factor = st.slider(
    "⚡ What-If Scenario: Simulated Growth/Decrease (%)",
    min_value=-50,
    max_value=100,
    value=0,
    step=5,
    help="Adjust forecast baseline dynamically based on market assumptions."
)

# -----------------------------------
# Load Forecasts from Snowflake
# -----------------------------------

forecast_df = get_future_forecasts()

if forecast_df.empty:

    st.warning("No forecast data available.")

else:

    # -----------------------------------
    # Prepare Historical Data
    # -----------------------------------

    historical_df = monthly_df.copy()

    historical_df["Period"] = pd.to_datetime(
        historical_df["year"].astype(str)
        + "-"
        + historical_df["month"].astype(str)
        + "-01"
    )

    # -----------------------------------
    # Prepare Forecast Data
    # -----------------------------------

    forecast_df["FORECAST_DATE"] = pd.to_datetime(
        forecast_df["FORECAST_DATE"]
    )

    forecast_df = forecast_df.rename(
        columns={
            "FORECAST_DATE": "Period",
            "MODEL_NAME": "Model",
            "FORECAST_REVENUE": "Forecast"
        }
    )
    # -----------------------------------
    # What-If Scenario
    # -----------------------------------

    multiplier = 1 + (growth_factor / 100.0)

    forecast_df["Simulated_Forecast"] = (
        forecast_df["Forecast"] * multiplier
    )

    # -----------------------------------
    # Forecast Chart
    # -----------------------------------

    import plotly.graph_objects as go

    fig_fc = go.Figure()

    # Historical Revenue
    fig_fc.add_trace(
        go.Scatter(
            x=historical_df["Period"],
            y=historical_df["revenue"],
            mode="lines+markers",
            name="Historical Revenue"
        )
    )

    # Model Forecasts
    for model in forecast_df["Model"].unique():

        model_df = forecast_df[
            forecast_df["Model"] == model
        ]

        fig_fc.add_trace(
            go.Scatter(
                x=model_df["Period"],
                y=model_df["Forecast"],
                mode="lines+markers",
                name=f"{model} Forecast"
            )
        )

        # What-If
        if growth_factor != 0:

            fig_fc.add_trace(
                go.Scatter(
                    x=model_df["Period"],
                    y=model_df["Simulated_Forecast"],
                    mode="lines+markers",
                    name=f"{model} Simulated ({growth_factor:+d}%)",
                    line=dict(dash="dot")
                )
            )

    fig_fc.update_layout(
        template="plotly_dark",
        height=500,
        title=dict(
            text="Historical Revenue vs Model Forecast",
            x=0
        ),
        xaxis=dict(
            title="Date"
        ),
        yaxis=dict(
            title="Revenue (₹)"
        ),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(
            l=40,
            r=30,
            t=70,
            b=40
        )
    )

    st.plotly_chart(
        fig_fc,
        use_container_width=True
    )

    # -----------------------------------
    # Forecast Details
    # -----------------------------------

    st.markdown("### 📊 Forecast Details")

    display_forecast = forecast_df.copy()

    display_forecast["Forecast"] = (
        display_forecast["Forecast"].round(2)
    )

    display_forecast["Simulated_Forecast"] = (
        display_forecast["Simulated_Forecast"].round(2)
    )

    display_forecast["Period"] = (
        pd.to_datetime(display_forecast["Period"])
        .dt.strftime("%b %Y")
    )

    display_forecast = display_forecast.rename(
        columns={
            "Forecast": "Forecast Revenue",
            "Simulated_Forecast": "What-If Revenue"
        }
    )

    display_forecast = display_forecast[
        [
            "Period",
            "Model",
            "Forecast Revenue",
            "What-If Revenue"
        ]
    ]

    st.dataframe(
        display_forecast,
        use_container_width=True,
        hide_index=True
    )

st.divider()

# -----------------------------------
# AI Insights & Executive Summary
# -----------------------------------
st.subheader("🤖 AI Business Insights")
insights = business_insights(selected_country)

rev_val = insights.iloc[0]["revenue"]
avg_ord = insights.iloc[0]["avg_order"]
max_val = insights.iloc[0]["max_sale"]

c1, c2, c3 = st.columns(3)
insight_cards = [
    ("💰", "Total Revenue", f"₹{rev_val:,.2f}", "#16A34A"),
    ("📦", "Average Order", f"₹{avg_ord:,.2f}", "#2563EB"),
    ("🚀", "Highest Sale", f"₹{max_val:,.2f}", "#EA580C")
]

for col, (icon, title, value, color) in zip([c1, c2, c3], insight_cards):
    with col:
        st.markdown(f"""
        <div style="background:white; border-radius:15px; padding:18px; border-left:6px solid {color}; box-shadow:0px 4px 12px rgba(0,0,0,0.12);">
            <div style="font-size:28px;">{icon}</div>
            <div style="color:#666; font-size:15px; font-weight:600; margin-top:8px;">{title}</div>
            <div style="color:{color}; font-size:28px; font-weight:bold; margin-top:12px;">{value}</div>
        </div>
        """, unsafe_allow_html=True)

top_market = country_df.iloc[0]["country"] if selected_country == "All" and not country_df.empty else selected_country

st.divider()
st.subheader("📋 Executive Summary")
st.markdown(f"""
<div style="background:#ffffff; padding:25px; border-radius:15px; border-left:8px solid #2563EB; box-shadow:0px 4px 12px rgba(0,0,0,0.10); color:#000;">
<p style="font-size:17px; color:black;">💰 <b>Total Revenue:</b> ₹{rev_val:,.2f}</p>
<p style="font-size:17px; color:black;">📦 <b>Total Orders:</b> {orders:,}</p>
<p style="font-size:17px; color:black;">👥 <b>Total Customers:</b> {customers:,}</p>
<p style="font-size:17px; color:black;">🌍 <b>Selected Country:</b> {selected_country}</p>
<p style="font-size:17px; color:black;">🏆 <b>Top Market:</b> {top_market}</p>
<p style="font-size:17px; color:black;">🔮 <b>Forecast Status:</b> Next 3 Months Generated Successfully</p>
<p style="font-size:17px; color:black;">🤖 <b>AI Insights:</b> Updated Successfully</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# -----------------------------------
# Choropleth Map
# -----------------------------------
st.markdown("## 🌍 Global Revenue Distribution")
world_df = world_revenue()

fig_map = px.choropleth(
    world_df,
    locations="country",
    locationmode="country names",
    color="revenue",
    hover_name="country",
    color_continuous_scale="Blues",
    title="Revenue by Country"
)
fig_map.update_layout(template="plotly_white", height=600, title_x=0.5, margin=dict(l=0, r=0, t=60, b=0))
st.plotly_chart(fig_map, use_container_width=True)

st.divider()

st.markdown("""
<div style="text-align:center; color:#9CA3AF; font-size:15px; padding:15px;">
🚀 Built with <b>Python</b> • <b>PySpark</b> • <b>Snowflake</b> • <b>Streamlit</b> • <b>Plotly</b><br>
© 2026 Retail Analytics & Revenue Forecasting Platform 2.0
</div>
""", unsafe_allow_html=True)