import pandas as pd

def clean_data(df):

    print("\n========== DATA QUALITY REPORT ==========\n")

    print(f"Rows Before Cleaning : {len(df)}")

    print("\nMissing Values")
    print(df.isnull().sum())

    duplicates = df.duplicated().sum()
    print(f"\nDuplicate Rows : {duplicates}")

    df = df.drop_duplicates()

    # Remove invalid quantities
    df = df[df["Quantity"] > 0]

    # Remove invalid prices
    df = df[df["UnitPrice"] > 0]

    # Convert date correctly
    df["InvoiceDate"] = pd.to_datetime(
        df["InvoiceDate"],
        dayfirst=True,
        errors="coerce"
    )

    # Remove invalid dates
    df = df.dropna(subset=["InvoiceDate"])

    print(f"\nRows After Cleaning : {len(df)}")

    print("\nData Types")
    print(df.dtypes)

    print("\n✅ Data validation completed successfully.")

    return df