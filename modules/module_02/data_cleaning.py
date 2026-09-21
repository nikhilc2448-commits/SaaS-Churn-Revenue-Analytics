from pathlib import Path
import pandas as pd
from modules.module_01.data_loader import load_all_data

# Set the project root and output folder for cleaned datasets.
BASE = Path(__file__).resolve().parents[2]
CLEAN = BASE / "data" / "cleaned"
CLEAN.mkdir(parents=True, exist_ok=True)

# Basic cleanup for each table: remove duplicates and standardize text fields.
def clean(df):
    df = df.drop_duplicates()
    for c in df.select_dtypes(include=["object", "string"]):
        df[c] = df[c].astype("string").str.strip().str.title()
    return df

# Read all source tables.
tables = load_all_data()

# Clean customer records and standardize key fields.
customers = clean(tables["saas_customers"])
customers["Industry"] = customers["Industry"].fillna("Unknown")
customers["EmployeeCount"] = customers["EmployeeCount"].fillna(customers["EmployeeCount"].median())
customers["SignupDate"] = pd.to_datetime(customers["SignupDate"])

# Keep a set of valid customer IDs for matching downstream records.
valid_ids = set(customers["CustomerID"].str.upper())

# Clean subscription data and flag customers that do not match the master list.
subs = clean(tables["saas_subscriptions"])
subs["CustomerID"] = subs["CustomerID"].str.upper()
subs["Seats"] = subs["Seats"].fillna(subs["Seats"].median())
subs["MRR"] = subs["MRR"].fillna(subs["MRR"].median())
subs["StartDate"] = pd.to_datetime(subs["StartDate"])
subs["EndDate"] = pd.to_datetime(subs["EndDate"])
subs["CustomerMatchStatus"] = subs["CustomerID"].isin(valid_ids).map({True:"Matched",False:"Orphan"})

# Clean usage metrics and convert date values to datetime.
usage = clean(tables["saas_usage"])
usage["CustomerID"] = usage["CustomerID"].str.upper()
usage["ActiveUsers"] = usage["ActiveUsers"].fillna(usage["ActiveUsers"].median())
usage["SessionMinutes"] = usage["SessionMinutes"].fillna(usage["SessionMinutes"].median())
usage["Month"] = pd.to_datetime(usage["Month"])

# Clean support tickets and standardize key fields.
tickets = clean(tables["saas_tickets"])
tickets["CustomerID"] = tickets["CustomerID"].str.upper()
tickets["ResolutionHours"] = tickets["ResolutionHours"].fillna(tickets["ResolutionHours"].median())
tickets["SatisfactionScore"] = tickets["SatisfactionScore"].fillna(tickets["SatisfactionScore"].median())
tickets["OpenedDate"] = pd.to_datetime(tickets["OpenedDate"])

# Save all cleaned tables to the data/cleaned folder.
for name, df in {
    "saas_customers": customers,
    "saas_subscriptions": subs,
    "saas_usage": usage,
    "saas_tickets": tickets
}.items():
    df.to_csv(CLEAN / f"{name}_cleaned.csv", index=False)

print("Module 2 completed successfully.")