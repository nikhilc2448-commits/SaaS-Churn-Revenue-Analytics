from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "data" / "cleaned"
REPORTS = BASE / "reports"
REPORTS.mkdir(exist_ok=True)

# Load cleaned data
cust = pd.read_csv(DATA/"saas_customers_cleaned.csv")
sub = pd.read_csv(DATA/"saas_subscriptions_cleaned.csv")
use = pd.read_csv(DATA/"saas_usage_cleaned.csv")
tic = pd.read_csv(DATA/"saas_tickets_cleaned.csv")

# Customer-level summary
sub_sum = sub.groupby("CustomerID").agg(
    TotalMRR=("MRR","sum"),
    Seats=("Seats","sum"),
    Plan=("PlanName","last"),
    Status=("Status","last")
).reset_index()

use_sum = use.groupby("CustomerID").agg(
    Logins=("Logins","mean"),
    SessionMinutes=("SessionMinutes","mean")
).reset_index()

tic_sum = tic.groupby("CustomerID").agg(
    Tickets=("TicketID","count"),
    Satisfaction=("SatisfactionScore","mean")
).reset_index()

# LEFT JOIN
df = cust.merge(sub_sum,on="CustomerID",how="left") \
         .merge(use_sum,on="CustomerID",how="left") \
         .merge(tic_sum,on="CustomerID",how="left")

# Calculated columns
df["TenureMonths"] = (
    pd.Timestamp.today() - pd.to_datetime(df["SignupDate"])
).dt.days/30

df["RevenuePerSeat"] = df["TotalMRR"]/df["Seats"]
df["TicketsPerMonth"] = df["Tickets"]/df["TenureMonths"]

# GroupBy summary
industry = df.groupby("Industry").agg(
    Customers=("CustomerID","count"),
    Revenue=("TotalMRR","sum")
).reset_index()

# Pivot table
pivot = pd.pivot_table(
    df,
    index="Industry",
    columns="Plan",
    values="TotalMRR",
    aggfunc="sum",
    fill_value=0
)

# IQR outliers
q1,q3 = df["TotalMRR"].quantile([0.25,0.75])
iqr = q3-q1
df["Outlier"] = (
    (df["TotalMRR"]<q1-1.5*iqr) |
    (df["TotalMRR"]>q3+1.5*iqr)
)

# Correlation
corr = df[["TotalMRR","Seats","Logins","SessionMinutes"]].corr()

# Save
df.to_csv(REPORTS/"module4_customer_view.csv",index=False)
industry.to_csv(REPORTS/"module4_industry_summary.csv",index=False)
pivot.to_csv(REPORTS/"module4_pivot_table.csv")
corr.to_csv(REPORTS/"module4_correlation.csv")

print("Module 4 completed successfully.")
print(f"Customers: {len(df)} | Industries: {len(industry)}")