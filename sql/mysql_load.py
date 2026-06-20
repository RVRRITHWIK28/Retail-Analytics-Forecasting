import pandas as pd
from sqlalchemy import create_engine

df = pd.read_csv("data/cleaned_retail_data.csv")

engine = create_engine(
    "mysql+pymysql://root:9440211075%40Rv@127.0.0.1:3306/retail_analytics"
)

df.to_sql(
    name="retail_sales_full",
    con=engine,
    if_exists="replace",
    index=False,
    chunksize=10000
)

print("Data loaded successfully!")