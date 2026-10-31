import logging
from pathlib import Path
from typing import Dict, Union, Any, List
import numpy as np
import pandas as pd
import scipy.stats as stats
import joblib

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Recommender_Engine')

def calculate_value_at_risk(returns_series: pd.Series, confidence_level: float = 0.95) -> Dict[str, float]:
    clean_ret = returns_series.dropna()
    if len(clean_ret) < 10:
        return {"historical_var": 0.0, "parametric_var": 0.0}

    hist_var = float(-np.percentile(clean_ret, 100.0 * (1.0 - confidence_level)))

    mu = float(clean_ret.mean())
    sigma = float(clean_ret.std())
    z = float(stats.norm.ppf(1.0 - confidence_level))
    param_var = float(-(mu + z * sigma))

    return {
        "confidence_level": confidence_level,
        "historical_var": hist_var,
        "parametric_var": param_var
    }

def calculate_monthly_cohort_retention(df_txn: pd.DataFrame) -> pd.DataFrame:
    df = df_txn.copy()
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    df['order_month'] = df['transaction_date'].dt.to_period('M')
    df['cohort'] = df.groupby('investor_id')['transaction_date'].transform('min').dt.to_period('M')

    cohort_group = df.groupby(['cohort', 'order_month']).agg(n_investors=('investor_id', 'nunique')).reset_index()
    cohort_group['period_number'] = (cohort_group['order_month'] - cohort_group['cohort']).apply(lambda x: x.n)
    
    cohort_pivot = cohort_group.pivot(index='cohort', columns='period_number', values='n_investors')
    cohort_size = cohort_pivot.iloc[:, 0]
    retention_matrix = cohort_pivot.divide(cohort_size, axis=0) * 100.0
    return retention_matrix

def train_clustering(data_path: Union[str, Path] = None, models_dir: Union[str, Path] = None, processed_dir: Union[str, Path] = None) -> pd.DataFrame:
    base_dir = Path(__file__).resolve().parent.parent
    if data_path is None:
        data_path = base_dir / "data" / "raw" / "08_investor_transactions.csv"
    else:
        data_path = Path(data_path)
    if models_dir is None:
        models_dir = base_dir / "data" / "processed"
    else:
        models_dir = Path(models_dir)
    if processed_dir is None:
        processed_dir = base_dir / "data" / "processed"
    else:
        processed_dir = Path(processed_dir)

    models_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    df_txn = pd.read_csv(data_path)
    df = df_txn.groupby('investor_id').agg(
        total_invested=('amount_inr', 'sum'),
        txn_count=('amount_inr', 'count'),
        annual_income=('annual_income_lakh', 'max')
    ).reset_index()

    features = ['total_invested', 'txn_count', 'annual_income']
    X = df[features]
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df['cluster'] = kmeans.fit_predict(X_scaled)
    sil_score = float(silhouette_score(X_scaled, df['cluster']))
    assert sil_score > 0.3

    cluster_labels = {0: 'Moderate Retail', 1: 'Affluent HNI', 2: 'Emerging Youth'}
    df['cluster_label'] = df['cluster'].map(cluster_labels)

    joblib.dump(kmeans, models_dir / "investor_kmeans_model.pkl")
    joblib.dump(scaler, models_dir / "investor_scaler.pkl")
    df.to_csv(processed_dir / "clustered_investors.csv", index=False)
    return df

class InvestorSegmenter:
    EXPECTED_FEATURES = ['total_invested', 'txn_count', 'annual_income']
    CLUSTER_LABELS = {
        0: 'Moderate Retail',
        1: 'Affluent HNI',
        2: 'Emerging Youth'
    }

    def __init__(self, models_dir: Union[str, Path] = None):
        base_dir = Path(__file__).resolve().parent.parent
        if models_dir is None:
            self.models_path = base_dir / "data" / "processed"
        else:
            self.models_path = Path(models_dir)

        try:
            self.scaler = joblib.load(self.models_path / 'investor_scaler.pkl')
            self.kmeans = joblib.load(self.models_path / 'investor_kmeans_model.pkl')
            logger.info("Successfully loaded ML models (Scaler & KMeans).")
        except FileNotFoundError:
            logger.info("Model files not found. Training K-Means models now...")
            train_clustering(models_dir=self.models_path)
            self.scaler = joblib.load(self.models_path / 'investor_scaler.pkl')
            self.kmeans = joblib.load(self.models_path / 'investor_kmeans_model.pkl')

    def predict_cluster(self, investor_data: Union[Dict[str, float], pd.DataFrame]) -> Dict[str, Any]:
        if isinstance(investor_data, dict):
            df_input = pd.DataFrame([investor_data])
        else:
            df_input = investor_data.copy()

        missing_features = [f for f in self.EXPECTED_FEATURES if f not in df_input.columns]
        if missing_features:
            raise ValueError(f"Missing required features for inference: {missing_features}")

        df_input = df_input[self.EXPECTED_FEATURES]
        X_scaled = self.scaler.transform(df_input)
        cluster_id = int(self.kmeans.predict(X_scaled)[0])
        label = self.CLUSTER_LABELS.get(cluster_id, "Standard Retail")
        
        return {
            "cluster_id": cluster_id,
            "cluster_label": label
        }

def recommend_funds(investor_profile: Dict[str, Any], performance_df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    df = performance_df.copy()
    
    df['rank_return'] = df['return_3yr_pct'].rank(ascending=False)
    df['rank_sharpe'] = df['sharpe_ratio'].rank(ascending=False)
    df['rank_alpha'] = df['alpha'].rank(ascending=False)
    df['rank_expense'] = df['expense_ratio_pct'].rank(ascending=True)
    
    cluster_label = investor_profile.get('cluster_label', 'Moderate Retail')
    
    if cluster_label == 'Affluent HNI':
        df['composite_score'] = (
            df['rank_return'] * 0.35 +
            df['rank_alpha'] * 0.30 +
            df['rank_sharpe'] * 0.25 +
            df['rank_expense'] * 0.10
        )
    elif cluster_label == 'Emerging Youth':
        df['composite_score'] = (
            df['rank_return'] * 0.40 +
            df['rank_sharpe'] * 0.30 +
            df['rank_expense'] * 0.20 +
            df['rank_alpha'] * 0.10
        )
    else:
        df['composite_score'] = (
            df['rank_sharpe'] * 0.40 +
            df['rank_return'] * 0.25 +
            df['rank_expense'] * 0.25 +
            df['rank_alpha'] * 0.10
        )
        
    recommended = df.sort_values(by='composite_score').head(top_n)
    display_cols = [c for c in ['amfi_code', 'scheme_name', 'category', 'fund_house', 'return_3yr_pct', 'sharpe_ratio', 'alpha', 'expense_ratio_pct', 'composite_score'] if c in recommended.columns]
    return recommended[display_cols]

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    perf_path = base_dir / "data" / "processed" / "fact_performance.csv"
    txn_path = base_dir / "data" / "processed" / "fact_transactions.csv"
    
    segmenter = InvestorSegmenter()
    mock_investor = {
        'total_invested': 1500000.0,
        'txn_count': 14,
        'annual_income': 35.0
    }
    seg_res = segmenter.predict_cluster(mock_investor)
    print("Inference Segment:", seg_res)
    
    if perf_path.exists():
        df_perf = pd.read_csv(perf_path)
        recs = recommend_funds(seg_res, df_perf, top_n=5)
        print("Top 5 Recommendations:\n", recs)
        
    if txn_path.exists():
        df_t = pd.read_csv(txn_path)
        ret_matrix = calculate_monthly_cohort_retention(df_t)
        print("Cohort Retention Matrix (Sample):\n", ret_matrix.iloc[:3, :4])
