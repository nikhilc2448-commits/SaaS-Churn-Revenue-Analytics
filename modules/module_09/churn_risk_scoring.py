from pathlib import Path
import pandas as pd
import numpy as np

BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "data" / "cleaned"
REPORT = BASE / "reports"
REPORT.mkdir(exist_ok=True)

# Load data
cust = pd.read_csv(DATA/"saas_customers_cleaned.csv")
sub = pd.read_csv(DATA/"saas_subscriptions_cleaned.csv")
use = pd.read_csv(DATA/"saas_usage_cleaned.csv")
tic = pd.read_csv(DATA/"saas_tickets_cleaned.csv")

# Customer features
mrr = sub.groupby("CustomerID")["MRR"].sum().reset_index(name="TotalMRR")
usage = use.groupby("CustomerID")[["Logins","ActiveUsers","SessionMinutes"]].mean().reset_index()
ticket = tic.groupby("CustomerID").agg(
    TicketCount=("TicketID","count"),
    Satisfaction=("SatisfactionScore","mean")
).reset_index()

df = cust[["CustomerID","CompanyName"]].merge(mrr,on="CustomerID") \
                                       .merge(usage,on="CustomerID") \
                                       .merge(ticket,on="CustomerID")

# Risk score
score = (
    (df.Logins <= df.Logins.quantile(.25))*20 +
    (df.ActiveUsers <= df.ActiveUsers.quantile(.25))*20 +
    (df.SessionMinutes <= df.SessionMinutes.quantile(.25))*20 +
    (df.TicketCount >= df.TicketCount.quantile(.75))*20 +
    (df.Satisfaction <= df.Satisfaction.quantile(.25))*20
)

df["RiskScore"] = score

df["RiskLevel"] = np.select(
    [score>=80, score>=60, score>=40, score>=20],
    ["Critical","High","Medium","Low"],
    default="Minimal"
)

# Reports
summary = df.groupby("RiskLevel").agg(
    Customers=("CustomerID","count"),
    TotalMRR=("TotalMRR","sum")
).reset_index()

top10 = df.sort_values("RiskScore", ascending=False).head(10)

df.to_csv(REPORT/"module9_risk_scores.csv", index=False)
summary.to_csv(REPORT/"module9_risk_summary.csv", index=False)
top10.to_csv(REPORT/"module9_top10_risk.csv", index=False)

print("Module 9 completed successfully.")
print(f"Customers: {len(df)} | Critical: {(df.RiskLevel=='Critical').sum()}")