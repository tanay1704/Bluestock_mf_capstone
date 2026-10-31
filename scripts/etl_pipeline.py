import os
import logging
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ETL_Pipeline')

def run_etl() -> None:
    try:
        base_dir = Path(__file__).resolve().parent.parent
        raw_path = base_dir / "data" / "raw"
        processed_path = base_dir / "data" / "processed"
        db_dir = base_dir / "data" / "db"
        
        processed_path.mkdir(parents=True, exist_ok=True)
        db_dir.mkdir(parents=True, exist_ok=True)
        
        default_db_path = db_dir / "bluestock_mf.db"
        db_url = os.environ.get('DATABASE_URL', f"sqlite:///{default_db_path.as_posix()}")
        if db_url.startswith('sqlite:///db/'):
            db_url = f"sqlite:///{default_db_path.as_posix()}"

        engine = create_engine(db_url)
        logger.info(f"Connecting to database at {db_url}")

        schema_file = base_dir / "sql" / "schema.sql"
        if schema_file.exists():
            schema_sql = schema_file.read_text(encoding="utf-8")
            with engine.connect() as conn:
                conn.execute(text("PRAGMA foreign_keys = OFF;"))
                conn.execute(text("DROP TABLE IF EXISTS fact_nav;"))
                conn.execute(text("DROP TABLE IF EXISTS fact_transactions;"))
                conn.execute(text("DROP TABLE IF EXISTS fact_performance;"))
                conn.execute(text("DROP TABLE IF EXISTS fact_aum;"))
                conn.execute(text("DROP TABLE IF EXISTS clustered_investors;"))
                conn.execute(text("DROP TABLE IF EXISTS dim_date;"))
                conn.execute(text("DROP TABLE IF EXISTS dim_fund;"))
                for statement in schema_sql.split(";"):
                    stmt = statement.strip()
                    if stmt:
                        conn.execute(text(stmt))
                conn.execute(text("PRAGMA foreign_keys = ON;"))
                conn.commit()

        df_fund = pd.read_csv(raw_path / "01_fund_master.csv")
        df_fund['amfi_code'] = df_fund['amfi_code'].astype(int)
        df_fund = df_fund.drop_duplicates(subset=['amfi_code'])
        df_fund.to_csv(processed_path / "01_fund_master.csv", index=False)
        df_fund.to_csv(processed_path / "dim_fund.csv", index=False)
        df_fund.to_sql("dim_fund", engine, if_exists="append", index=False)

        df_txn = pd.read_csv(raw_path / "08_investor_transactions.csv")
        df_txn['transaction_date'] = pd.to_datetime(df_txn['transaction_date'])
        df_txn['amount_inr'] = pd.to_numeric(df_txn['amount_inr'], errors='coerce')
        assert (df_txn['amount_inr'] > 0).all()
        df_txn['transaction_type'] = df_txn['transaction_type'].astype(str).str.strip()
        valid_types = {'SIP', 'Lumpsum', 'Redemption'}
        assert set(df_txn['transaction_type'].unique()).issubset(valid_types)
        valid_kyc = {'Verified', 'Pending'}
        assert set(df_txn['kyc_status'].dropna().unique()).issubset(valid_kyc)
        df_txn['date_key'] = df_txn['transaction_date'].dt.strftime('%Y-%m-%d')

        df_nav = pd.read_csv(raw_path / "02_nav_history.csv")
        df_nav['date'] = pd.to_datetime(df_nav['date'])
        df_nav['amfi_code'] = df_nav['amfi_code'].astype(int)
        df_nav['nav'] = pd.to_numeric(df_nav['nav'], errors='coerce')
        df_nav = df_nav.drop_duplicates(subset=['amfi_code', 'date']).sort_values(['amfi_code', 'date'])

        reindexed_groups = []
        for amfi, group in df_nav.groupby('amfi_code'):
            min_d, max_d = group['date'].min(), group['date'].max()
            cal_idx = pd.date_range(min_d, max_d, freq='D', name='date')
            g = group.set_index('date').reindex(cal_idx)
            g['amfi_code'] = amfi
            g['nav'] = g['nav'].ffill().bfill()
            g = g.reset_index()
            g['daily_return_pct'] = g['nav'].pct_change() * 100.0
            reindexed_groups.append(g)

        df_nav_clean = pd.concat(reindexed_groups, ignore_index=True)
        assert (df_nav_clean['nav'] > 0).all()
        df_nav_clean.rename(columns={'date': 'nav_date'}, inplace=True)
        df_nav_clean['date_key'] = df_nav_clean['nav_date'].dt.strftime('%Y-%m-%d')

        all_dates = pd.concat([
            pd.Series(df_txn['transaction_date'].dt.date.unique()),
            pd.Series(df_nav_clean['nav_date'].dt.date.unique())
        ]).drop_duplicates().sort_values()
        
        min_date = all_dates.min()
        max_date = all_dates.max()
        full_date_range = pd.date_range(min_date, max_date, freq='D')
        df_date = pd.DataFrame({'full_date': full_date_range})
        df_date['date_key'] = df_date['full_date'].dt.strftime('%Y-%m-%d')
        df_date['year'] = df_date['full_date'].dt.year
        df_date['quarter'] = df_date['full_date'].dt.quarter
        df_date['month'] = df_date['full_date'].dt.month
        df_date['month_name'] = df_date['full_date'].dt.strftime('%B')
        df_date['day'] = df_date['full_date'].dt.day
        df_date['day_of_week'] = df_date['full_date'].dt.dayofweek
        df_date['day_name'] = df_date['full_date'].dt.strftime('%A')
        df_date['is_weekend'] = df_date['day_of_week'].isin([5, 6]).astype(int)
        df_date.to_csv(processed_path / "dim_date.csv", index=False)
        df_date.to_sql("dim_date", engine, if_exists="append", index=False)

        df_perf = pd.read_csv(raw_path / "07_scheme_performance.csv")
        df_perf['amfi_code'] = df_perf['amfi_code'].astype(int)
        df_perf['expense_ratio_pct'] = df_perf['expense_ratio_pct'].astype(float)
        assert ((df_perf['expense_ratio_pct'] >= 0.1) & (df_perf['expense_ratio_pct'] <= 2.5)).all()
        for col in ['return_1yr_pct', 'return_3yr_pct', 'return_5yr_pct', 'benchmark_3yr_pct']:
            if col in df_perf.columns:
                df_perf[col] = pd.to_numeric(df_perf[col], errors='coerce')
        df_perf = df_perf.drop_duplicates(subset=['amfi_code'])
        df_perf.to_csv(processed_path / "07_scheme_performance.csv", index=False)
        df_perf.to_csv(processed_path / "fact_performance.csv", index=False)
        df_perf.to_sql("fact_performance", engine, if_exists="append", index=False)

        df_nav_clean.to_csv(processed_path / "02_nav_history.csv", index=False)
        df_nav_clean.to_csv(processed_path / "fact_nav.csv", index=False)
        df_nav_clean.to_sql("fact_nav", engine, if_exists="append", index=False)

        df_txn.to_csv(processed_path / "08_investor_transactions.csv", index=False)
        df_txn.to_csv(processed_path / "fact_transactions.csv", index=False)
        df_txn.to_sql("fact_transactions", engine, if_exists="append", index=False)

        df_aum = pd.read_csv(raw_path / "03_aum_by_fund_house.csv")
        df_aum['report_date'] = pd.to_datetime(df_aum['date'])
        df_aum['date_key'] = df_aum['report_date'].dt.strftime('%Y-%m-%d')
        df_aum['aum_crore'] = df_aum['aum_crore'].astype(int)
        df_aum['aum_lakh_crore'] = df_aum['aum_lakh_crore'].astype(float)
        df_aum.to_csv(processed_path / "03_aum_by_fund_house.csv", index=False)
        df_aum.to_csv(processed_path / "fact_aum.csv", index=False)
        df_aum[['report_date', 'date_key', 'fund_house', 'aum_lakh_crore', 'aum_crore', 'num_schemes']].to_sql("fact_aum", engine, if_exists="append", index=False)

        df_sip = pd.read_csv(raw_path / "04_monthly_sip_inflows.csv")
        df_sip.to_csv(processed_path / "04_monthly_sip_inflows.csv", index=False)

        df_cat = pd.read_csv(raw_path / "05_category_inflows.csv")
        df_cat.to_csv(processed_path / "05_category_inflows.csv", index=False)

        df_folio = pd.read_csv(raw_path / "06_industry_folio_count.csv")
        df_folio.to_csv(processed_path / "06_industry_folio_count.csv", index=False)

        df_holdings = pd.read_csv(raw_path / "09_portfolio_holdings.csv")
        df_holdings.to_csv(processed_path / "09_portfolio_holdings.csv", index=False)

        df_bench = pd.read_csv(raw_path / "10_benchmark_indices.csv")
        df_bench.to_csv(processed_path / "10_benchmark_indices.csv", index=False)

        clustered_path = processed_path / "clustered_investors.csv"
        if clustered_path.exists():
            df_clusters = pd.read_csv(clustered_path)
            cluster_labels = {0: 'Moderate Retail', 1: 'Affluent HNI', 2: 'Emerging Youth'}
            if 'cluster_label' not in df_clusters.columns:
                df_clusters['cluster_label'] = df_clusters['cluster'].map(cluster_labels)
            df_clusters.to_csv(clustered_path, index=False)
            df_clusters.to_sql("clustered_investors", engine, if_exists="append", index=False)

        with engine.connect() as conn:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_dim_fund_amfi ON dim_fund(amfi_code);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_dim_date_key ON dim_date(date_key);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fact_perf_amfi ON fact_performance(amfi_code);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fact_perf_return ON fact_performance(return_3yr_pct);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fact_nav_amfi ON fact_nav(amfi_code);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fact_nav_date ON fact_nav(nav_date);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fact_txn_amfi ON fact_transactions(amfi_code);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fact_txn_investor ON fact_transactions(investor_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fact_txn_date ON fact_transactions(transaction_date);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fact_txn_type ON fact_transactions(transaction_type);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fact_aum_date ON fact_aum(report_date);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fact_aum_fh ON fact_aum(fund_house);"))
            conn.commit()

        logger.info("ETL Pipeline execution completed successfully.")
    except Exception as e:
        logger.error(f"ETL Pipeline execution failed: {str(e)}", exc_info=True)
        raise

def export_tables_to_csv(engine=None, processed_dir: Path = None) -> None:
    base_dir = Path(__file__).resolve().parent.parent
    if processed_dir is None:
        processed_dir = base_dir / "data" / "processed"
    else:
        processed_dir = Path(processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)
    if engine is None:
        default_db_path = base_dir / "data" / "db" / "bluestock_mf.db"
        db_url = os.environ.get('DATABASE_URL', f"sqlite:///{default_db_path.as_posix()}")
        if db_url.startswith('sqlite:///db/'):
            db_url = f"sqlite:///{default_db_path.as_posix()}"
        engine = create_engine(db_url)
    table_queries = {
        "dim_fund": text("SELECT * FROM dim_fund"),
        "dim_date": text("SELECT * FROM dim_date"),
        "fact_nav": text("SELECT * FROM fact_nav"),
        "fact_transactions": text("SELECT * FROM fact_transactions"),
        "fact_performance": text("SELECT * FROM fact_performance"),
        "fact_aum": text("SELECT * FROM fact_aum"),
        "clustered_investors": text("SELECT * FROM clustered_investors")
    }
    with engine.connect() as conn:
        for tbl_name, q in table_queries.items():
            try:
                df = pd.read_sql(q, conn)
                df.to_csv(processed_dir / f"{tbl_name}.csv", index=False)
            except Exception:
                continue

if __name__ == "__main__":
    run_etl()
