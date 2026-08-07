from extract import extract_data
from transform import clean_data

df = extract_data("data/raw/superstore.csv")

df = clean_data(df)

print(df.head())