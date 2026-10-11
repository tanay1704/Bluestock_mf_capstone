import os
from pathlib import Path
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import joblib

# Determine base and project directories
base_dir = Path(__file__).resolve().parent if "__file__" in locals() else Path.cwd()
if (base_dir / "data" / "raw" / "08_investor_transactions.csv").exists():
    data_path = base_dir / "data" / "raw" / "08_investor_transactions.csv"
    models_dir = base_dir / "models"
elif (base_dir.parent / "data" / "raw" / "08_investor_transactions.csv").exists():
    data_path = base_dir.parent / "data" / "raw" / "08_investor_transactions.csv"
    models_dir = base_dir.parent / "models"
else:
    data_path = Path("data/raw/08_investor_transactions.csv")
    models_dir = Path("models")

# Load investor transactions
df_txn = pd.read_csv(data_path)

# Aggregate transaction and income features per investor
df = df_txn.groupby('investor_id').agg(
    total_invested=('amount_inr', 'sum'),
    txn_count=('amount_inr', 'count'),
    annual_income=('annual_income_lakh', 'max')
).reset_index()

# Scale features
X = df[['total_invested', 'txn_count', 'annual_income']]
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Perform K-Means clustering
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
df['cluster'] = kmeans.fit_predict(X_scaled)

# Persist trained models
models_dir.mkdir(parents=True, exist_ok=True)
joblib.dump(kmeans, models_dir / "investor_kmeans_model.pkl")
joblib.dump(scaler, models_dir / "investor_scaler.pkl")

# Save final clustered dataframe
df.to_csv("clustered_investors.csv", index=False)
