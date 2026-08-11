import os
import streamlit as st
from sqlalchemy import create_engine

def get_database_url() -> str:
    # 1. Check Streamlit Cloud Secrets first
    if "DATABASE_URL" in st.secrets:
        return st.secrets["DATABASE_URL"]
    
    # 2. Check system/local environment variables
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    
    # 3. Fallback to local secrets dict format if st.secrets is structured
    if "postgres" in st.secrets:
        db = st.secrets["postgres"]
        return f"postgresql://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db['dbname']}?sslmode=require"

    raise ValueError("DATABASE_URL is not set in Streamlit Secrets or Environment Variables.")

# Initialize connection engine
DATABASE_URL = get_database_url()

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Checks connection health before executing queries
    pool_recycle=1800,   # Recycles connection every 30 minutes to match Neon timeouts
    pool_size=10,        # Keeps connection pool manageable on serverless instances
    max_overflow=20      # Allows bursts for concurrent user requests
)