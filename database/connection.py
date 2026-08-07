
from sqlalchemy import create_engine

DATABASE_URL = "postgresql://postgres:9440211075%40Rv@localhost:5432/retail_db"

engine = create_engine(DATABASE_URL)