from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# Paths
# -----------------------------
BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "data" / "cleaned"
REPORTS = BASE / "reports"
REPORTS.mkdir(exist_ok=True)

# -----------------------------
# Load data
# -----------------------------
customers = pd.read_csv(DATA / "saas_customers_cleaned.csv")
usage = pd.read_csv(DATA / "saas_usage_cleaned.csv")

customers["SignupDate"] = pd.to_datetime(customers["SignupDate"])
usage["Month"] = pd.to_datetime(usage["Month"])

# -----------------------------
# Cohort creation
# -----------------------------
customers["Cohort"] = customers["SignupDate"].dt.to_period("M")
usage["ActivityMonth"] = usage["Month"].dt.to_period("M")

df = usage.merge(
    customers[["CustomerID", "Cohort"]],
    on="CustomerID",
    how="left"
)

# Months since signup
df["MonthNo"] = (
    (df["ActivityMonth"].dt.year - df["Cohort"].dt.year) * 12 +
    (df["ActivityMonth"].dt.month - df["Cohort"].dt.month)
)

# Keep valid months only
df = df[df["MonthNo"] >= 0]

# -----------------------------
# Cohort retention table
# -----------------------------
retention = (
    df.groupby(["Cohort", "MonthNo"])["CustomerID"]
      .nunique()
      .reset_index(name="ActiveCustomers")
)

cohort_size = (
    customers.groupby("Cohort")["CustomerID"]
             .nunique()
             .reset_index(name="CohortSize")
)

retention = retention.merge(cohort_size, on="Cohort")

retention["RetentionRate"] = (
    retention["ActiveCustomers"] /
    retention["CohortSize"] * 100
).round(2)

# -----------------------------
# Retention matrix
# -----------------------------
retention_matrix = retention.pivot(
    index="Cohort",
    columns="MonthNo",
    values="RetentionRate"
)
# -----------------------------
# Overall retention curve
# -----------------------------
total_customers = customers["CustomerID"].nunique()

retention_curve = (
    df.groupby("MonthNo", as_index=False)["CustomerID"]
      .nunique()
      .rename(columns={"CustomerID": "ActiveCustomers"})
      .sort_values("MonthNo")
)

retention_curve["MonthNo"] = retention_curve["MonthNo"].astype(int)

retention_curve["RetentionRate"] = (
    retention_curve["ActiveCustomers"] / total_customers * 100
).round(2)

# -----------------------------
# Plot
# -----------------------------
plt.figure(figsize=(10, 6))

plt.plot(
    retention_curve["MonthNo"].values,
    retention_curve["RetentionRate"].values,
    marker="o",
    linewidth=2
)

plt.title("Customer Retention Curve")
plt.xlabel("Months Since Signup")
plt.ylabel("Retention Rate (%)")
plt.xticks(range(0, 24))
plt.xlim(0, 23)
plt.ylim(0, 100)
plt.grid(True, alpha=0.3)
plt.tight_layout()

plt.savefig(REPORTS / "module6_retention_curve.png")
plt.close()

# -----------------------------
# Best & Worst Cohort
# -----------------------------
month1 = retention[retention["MonthNo"] == 1]

best = month1.loc[month1["RetentionRate"].idxmax()]
worst = month1.loc[month1["RetentionRate"].idxmin()]

summary = pd.DataFrame({
    "Category": ["Best Cohort", "Worst Cohort"],
    "Cohort": [str(best["Cohort"]), str(worst["Cohort"])],
    "RetentionRate": [best["RetentionRate"], worst["RetentionRate"]]
})

# -----------------------------
# Output
# -----------------------------
print("\nModule 6 - Cohort & Retention Analysis")
print("-" * 40)
print(f"Total Cohorts   : {customers['Cohort'].nunique()}")
print(f"Total Customers : {total_customers}")
print(f"Best Cohort     : {best['Cohort']} ({best['RetentionRate']}%)")
print(f"Worst Cohort    : {worst['Cohort']} ({worst['RetentionRate']}%)")
print("Reports saved in reports folder.")

