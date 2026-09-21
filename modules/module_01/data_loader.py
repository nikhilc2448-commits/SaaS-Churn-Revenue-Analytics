from pathlib import Path
import pandas as pd

# Project path
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"

# Files to load
FILES = [
    "saas_customers.csv",
    "saas_subscriptions.csv",
    "saas_usage.csv",
    "saas_tickets.csv"
]

def load_all_data():
    """Load all SaaS CSV files."""

    data = {}

    for file in FILES:
        path = DATA_DIR / file

        if not path.exists():
            raise FileNotFoundError(f"{file} not found")

        df = pd.read_csv(path)

        if df.empty:
            raise ValueError(f"{file} is empty")

        print(f"{file}: {df.shape} ✓")

        data[file.replace(".csv", "")] = df

    return data


if __name__ == "__main__":
    print("Module 1 - Data Loader\n")
    load_all_data()
    print("\nAll datasets loaded successfully.")