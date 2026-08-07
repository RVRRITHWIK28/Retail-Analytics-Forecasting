import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import plotly.express as px

from services.dashboard_service import (
    get_kpis,
    get_countries,
    revenue_trend,
)

# --------------------------
# Page Config
# --------------------------

st.set_page_config(
    page_title="Retail Analytics Platform",
    page_icon="📊",
    layout="wide"
)

# --------------------------
# Header
# --------------------------

st.title("📊 Retail Analytics & Demand Forecasting Platform")

col1, col2 = st.columns([5, 1])

with col1:
    st.caption("Production-Level Business Intelligence Dashboard")

with col2:
    st.caption(datetime.now().strftime("%d-%b-%Y %I:%M %p"))

# --------------------------
# Sidebar
# --------------------------

st.sidebar.title("🔎 Filters")

countries = get_countries()

selected_country = st.sidebar.selectbox(
    "Select Country",
    ["All"] + countries
)

# --------------------------
# KPI Cards
# --------------------------

revenue, orders, customers, country_count = get_kpis(selected_country)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "💰 Revenue",
        f"₹{revenue:,.2f}"
    )

with c2:
    st.metric(
        "📦 Orders",
        f"{orders:,}"
    )

with c3:
    st.metric(
        "👥 Customers",
        f"{customers:,}"
    )

with c4:
    st.metric(
        "🌍 Countries",
        country_count
    )

st.divider()

# --------------------------
# Revenue Trend
# --------------------------

st.subheader("📈 Monthly Revenue Trend")

trend = revenue_trend(selected_country)

# Year + Month ni oka label ga create chestham
trend["Period"] = trend["month"].astype(str) + "-" + trend["year"].astype(str)

fig = px.line(
    trend,
    x="Period",
    y="revenue",
    markers=True,
    title=f"Revenue Trend - {selected_country}"
)

fig.update_layout(
    template="plotly_white",
    height=500,
    xaxis_title="Month",
    yaxis_title="Revenue"
)

st.plotly_chart(fig, use_container_width=True)