import pandas as pd

def extract_data(file_path):
    df = pd.read_csv(file_path)
    print(f"✅ Loaded {len(df)} rows.")
    return df

if __name__ == "__main__":
    df = extract_data("data/raw/superstore.csv")
    print(df.head())