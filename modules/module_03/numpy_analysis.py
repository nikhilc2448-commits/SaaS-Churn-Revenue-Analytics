from pathlib import Path
import numpy as np
import pandas as pd

# Paths
BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "data" / "cleaned"
REPORTS = BASE / "reports"
REPORTS.mkdir(exist_ok=True)

# ---------- Reusable Functions ----------
def load_csv(filename):
    path = DATA / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {filename}")
    return pd.read_csv(path)

def metric_stats(name, arr):
    return {
        "Metric": name,
        "Mean": round(np.mean(arr), 2),
        "Std": round(np.std(arr), 2),
        "Min": np.min(arr),
        "Max": np.max(arr)
    }

def min_max_normalize(series):
    return (series - series.min()) / (series.max() - series.min())

# ---------- Load Data ----------
subs = load_csv("saas_subscriptions_cleaned.csv")
usage = load_csv("saas_usage_cleaned.csv")

# ---------- NumPy Statistics ----------
metrics = {
    "MRR": subs["MRR"].to_numpy(),
    "Seats": subs["Seats"].to_numpy(),
    "Logins": usage["Logins"].to_numpy(),
    "ActiveUsers": usage["ActiveUsers"].to_numpy(),
    "APICalls": usage["APICalls"].to_numpy(),
    "SessionMinutes": usage["SessionMinutes"].to_numpy()
}

stats = pd.DataFrame(
    [metric_stats(name, values) for name, values in metrics.items()]
)

# ---------- Normalize MRR ----------
subs["NormalizedMRR"] = min_max_normalize(subs["MRR"]).round(3)

# ---------- Customer Flags ----------
customer = (
    subs.groupby("CustomerID", as_index=False)["MRR"]
        .sum()
        .rename(columns={"MRR": "TotalMRR"})
)

usage_avg = (
    usage.groupby("CustomerID", as_index=False)
         [["ActiveUsers", "SessionMinutes"]]
         .mean()
)

customer = customer.merge(usage_avg, on="CustomerID", how="left")

mrr_q3 = np.percentile(customer["TotalMRR"], 75)
active_q1 = np.percentile(customer["ActiveUsers"], 25)
session_q1 = np.percentile(customer["SessionMinutes"], 25)

customer["HighValue"] = np.where(customer["TotalMRR"] >= mrr_q3, "Yes", "No")
customer["AtRisk"] = np.where(
    (customer["ActiveUsers"] <= active_q1) &
    (customer["SessionMinutes"] <= session_q1),
    "Yes", "No"
)

customer["RiskScore"] = np.where(
    customer["HighValue"].eq("Yes") & customer["AtRisk"].eq("Yes"), 3,
    np.where(customer["AtRisk"].eq("Yes"), 2, 1)
)

# ---------- Save Reports ----------
stats.to_csv(REPORTS / "module3_numpy_statistics.csv", index=False)
customer.to_csv(REPORTS / "module3_numpy_customer_flags.csv", index=False)

# ---------- Summary ----------
print("\nModule 3 - NumPy Analysis")
print("-" * 35)
print(f"Metrics analysed : {len(metrics)}")
print(f"High-value       : {(customer['HighValue']=='Yes').sum()}")
print(f"At-risk          : {(customer['AtRisk']=='Yes').sum()}")
print(f"Avg MRR          : {stats.loc[0, 'Mean']}")