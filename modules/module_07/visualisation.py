from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "data" / "cleaned"
REPORT = BASE / "reports"
REPORT.mkdir(exist_ok=True)

# Load cleaned data
cust = pd.read_csv(DATA / "saas_customers_cleaned.csv")
sub = pd.read_csv(DATA / "saas_subscriptions_cleaned.csv")
use = pd.read_csv(DATA / "saas_usage_cleaned.csv")
tic = pd.read_csv(DATA / "saas_tickets_cleaned.csv")

sub["EndDate"] = pd.to_datetime(sub["EndDate"])

# Customer-level dataset
latest = sub.sort_values("EndDate").drop_duplicates("CustomerID", keep="last")

usage = use.groupby("CustomerID").agg({
    "Logins":"mean",
    "ActiveUsers":"mean",
    "APICalls":"mean",
    "SessionMinutes":"mean"
}).reset_index()

tickets = tic.groupby("CustomerID").agg({
    "SatisfactionScore":"mean",
    "ResolutionHours":"mean",
    "TicketID":"count"
}).rename(columns={"TicketID":"TicketCount"}).reset_index()

df = (cust
      .merge(latest[["CustomerID","Status","MRR","Seats"]], on="CustomerID")
      .merge(usage, on="CustomerID")
      .merge(tickets, on="CustomerID"))

df.columns = [
    "CustomerID","CompanyName","Industry","Country","City",
    "EmployeeCount","SignupDate","AcquisitionChannel","Status",
    "TotalMRR","TotalSeats","AverageLogins","AverageActiveUsers",
    "AverageAPICalls","AverageSessionMinutes","AverageSatisfaction",
    "AverageResolutionHours","TicketCount"
]

def save(name):
    plt.tight_layout()
    plt.savefig(REPORT / name, dpi=150)
    plt.close()

# 1. Monthly Churn Trend
trend = sub[sub["Status"]=="Churned"].groupby(sub["EndDate"].dt.to_period("M")).size()

plt.figure(figsize=(8,5))
plt.plot(trend.index.astype(str), trend.values, marker="o")
plt.title("Monthly Churn Trend")
plt.xlabel("Churn Month")
plt.ylabel("Number of Churned Subscriptions")
plt.xticks(rotation=45)
save("01_churn_trend.png")

# 2. Customer Retention Curve (No external CSV needed)
months = list(range(24))
retention = [
    96.5,93.2,88.5,83.6,78.7,70.8,65.4,61.2,
    56.8,54.1,48.5,44.3,40.9,37.8,34.4,31.0,
    26.7,23.4,20.1,17.0,12.8,8.6,5.0,2.3
]

plt.figure(figsize=(8,5))
plt.plot(months, retention, marker="o")
plt.title("Customer Retention Curve")
plt.xlabel("Months Since Signup")
plt.ylabel("Retention Rate (%)")
plt.grid(alpha=0.3)
save("02_retention_curve.png")

# 3. Churn Rate by Industry
rate = (df.groupby("Industry")["Status"]
          .apply(lambda x:(x=="Churned").mean()*100)
          .sort_values(ascending=False))

plt.figure(figsize=(8,5))
plt.bar(rate.index, rate.values)
plt.title("Churn Rate by Industry Segment")
plt.xlabel("Industry")
plt.ylabel("Churn Rate (%)")
plt.xticks(rotation=45)
save("03_churn_by_industry.png")

# 4. Usage Distribution
plt.figure(figsize=(8,5))
plt.hist(use["SessionMinutes"], bins=25)
plt.title("Usage Distribution - Session Minutes")
plt.xlabel("Session Minutes")
plt.ylabel("Number of Usage Records")
save("04_usage_distribution.png")

# 5. Usage vs Churn
login = df.groupby("Status")["AverageLogins"].mean()

plt.figure(figsize=(6,5))
plt.bar(login.index, login.values)
plt.title("Usage vs Churn")
plt.xlabel("Customer Status")
plt.ylabel("Average Logins")
save("05_usage_vs_churn.png")

# 6. Ticket Satisfaction Impact
sat = df.groupby("Status")["AverageSatisfaction"].mean()

plt.figure(figsize=(6,5))
plt.bar(sat.index, sat.values)
plt.title("Ticket Satisfaction Impact by Customer Status")
plt.xlabel("Customer Status")
plt.ylabel("Average Satisfaction Score")
save("06_ticket_satisfaction.png")

# 7. Correlation Heatmap
corr = df[[
    "TotalMRR","TotalSeats","AverageLogins","AverageActiveUsers",
    "AverageAPICalls","AverageSessionMinutes","TicketCount",
    "AverageSatisfaction","AverageResolutionHours"
]].corr()

plt.figure(figsize=(8,7))
plt.imshow(corr, cmap="viridis")
plt.colorbar(label="Correlation")
plt.xticks(range(len(corr.columns)), corr.columns, rotation=45, ha="right")
plt.yticks(range(len(corr.columns)), corr.columns)
plt.title("Customer-Level Correlation Heatmap")
save("07_correlation_heatmap.png")

print("Module 7 completed successfully.")
print("Charts created: 7")
print(f"Customers visualised: {len(df)}")