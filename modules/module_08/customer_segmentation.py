from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "data" / "cleaned"
REPORT = BASE / "reports"
REPORT.mkdir(exist_ok=True)

# Load data
sub = pd.read_csv(DATA/"saas_subscriptions_cleaned.csv")
use = pd.read_csv(DATA/"saas_usage_cleaned.csv")
tic = pd.read_csv(DATA/"saas_tickets_cleaned.csv")

# Customer features
df = sub.groupby("CustomerID").agg(
    MRR=("MRR","sum"),
    Seats=("Seats","sum")
).reset_index()

usage = use.groupby("CustomerID")[["Logins","ActiveUsers","SessionMinutes"]].mean().reset_index()
tickets = tic.groupby("CustomerID")["SatisfactionScore"].mean().reset_index()

df = df.merge(usage,on="CustomerID").merge(tickets,on="CustomerID")
df = df.fillna(0)

# Scale features
features = ["MRR","Seats","Logins","ActiveUsers","SessionMinutes","SatisfactionScore"]
X = StandardScaler().fit_transform(df[features])

# Elbow Method
inertia = []
for k in range(2,7):
    inertia.append(KMeans(n_clusters=k, random_state=42, n_init=10).fit(X).inertia_)

plt.plot(range(2,7), inertia, marker="o")
plt.title("Elbow Method")
plt.savefig(REPORT/"module8_elbow.png")
plt.close()

# K-Means
model = KMeans(n_clusters=4, random_state=42, n_init=10)
df["Cluster"] = model.fit_predict(X)

# Segment names
names = {
    0:"High Value",
    1:"Growing Users",
    2:"Low Engagement",
    3:"Support Heavy"
}
df["Segment"] = df["Cluster"].map(names)

# Cluster summary
summary = df.groupby("Segment").agg(
    Customers=("CustomerID","count"),
    AvgMRR=("MRR","mean"),
    AvgLogins=("Logins","mean")
).reset_index()

# Save
df.to_csv(REPORT/"module8_customer_segments.csv", index=False)
summary.to_csv(REPORT/"module8_cluster_summary.csv", index=False)

print("Module 8 completed successfully.")
print(f"Customers: {len(df)} | Segments: {df['Segment'].nunique()}")