from pathlib import Path
import pandas as pd
from scipy.stats import ttest_ind

# Define the folder paths used for data input and report output.
BASE_DIR = Path(__file__).resolve().parents[2]
DATA = BASE_DIR / "data" / "cleaned"
REPORTS = BASE_DIR / "reports"
REPORTS.mkdir(exist_ok=True)

# Load the cleaned subscription and usage data for analysis.
subs = pd.read_csv(DATA / "saas_subscriptions_cleaned.csv")
usage = pd.read_csv(DATA / "saas_usage_cleaned.csv")

# 1. Descriptive statistics
# Summarize the main numeric measures for a quick business overview.
stats = pd.concat(
    [subs[["MRR", "Seats"]], usage[["Logins", "ActiveUsers", "APICalls", "SessionMinutes"]]],
    axis=1
).describe().T
stats.to_csv(REPORTS / "module_5_statistics_summary.csv")

# 2. Population vs random samples
# Compare the full customer population to two random samples for a simple sampling check.
customer_mrr = subs.groupby("CustomerID")["MRR"].sum()
population_mean = customer_mrr.mean()
sample1 = customer_mrr.sample(30, random_state=42)
sample2 = customer_mrr.drop(sample1.index).sample(30, random_state=43)

sample_df = pd.DataFrame({
    "Group": ["Population", "Sample 1", "Sample 2"],
    "Mean": [population_mean, sample1.mean(), sample2.mean()]
})
sample_df.to_csv(REPORTS / "module_5_sample_comparison.csv", index=False)

# 3. Churn hypothesis test
# Test whether churned customers have meaningfully different login behavior than retained ones.
latest = subs.sort_values("StartDate").drop_duplicates("CustomerID", keep="last")
logins = usage.groupby("CustomerID")["Logins"].mean().reset_index()

data = latest[["CustomerID", "Status"]].merge(logins, on="CustomerID")
churned = data[data["Status"] == "Churned"]["Logins"]
retained = data[data["Status"] != "Churned"]["Logins"]

t_stat, p_value = ttest_ind(churned, retained, equal_var=False)

result = pd.DataFrame({
    "PValue": [p_value],
    "TStatistic": [t_stat]
})
result.to_csv(REPORTS / "module_5_churn_hypothesis.csv", index=False)

# Output summary for quick review in the terminal.
print("Module 5 - Statistics")
print(f"Population Mean MRR: {population_mean:.2f}")
print(f"Sample Size: 30")
print(f"P-value: {p_value:.4f}")
print("Reports saved successfully.")