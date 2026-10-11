import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure enterprise-grade logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('ETL_Pipeline')

def run_etl() -> None:
    """
    Extracts data from raw CSVs, transforms dates and NAV trends, 
    and loads the final structured tables into the SQLite database.
    
    Raises:
        Exception: If any error occurs during file reading, transformation, or database insertion.
    """
    try:
        BASE_DIR = Path(__file__).resolve().parent.parent
        raw_path = BASE_DIR / "data" / "raw"
        
        # Determine database URL from environment or default to local sqlite
        default_db_path = BASE_DIR / "db" / "bluestock_mf.db"
        db_url = os.environ.get('DATABASE_URL', f"sqlite:///{default_db_path}")
        
        # Ensure absolute path for sqlite if using relative in .env
        if db_url.startswith('sqlite:///db/'):
            db_url = f"sqlite:///{BASE_DIR / 'db' / 'bluestock_mf.db'}"

        (BASE_DIR / "db").mkdir(parents=True, exist_ok=True)
        engine = create_engine(db_url)
        
        logger.info(f"Connected to Database at {db_url}")

        # 1. Load Fund Master
        logger.info("Loading Fund Master...")
        df_fund = pd.read_csv(raw_path / "01_fund_master.csv")
        df_fund.to_sql("dim_fund", engine, if_exists="replace", index=False)
        
        # 2. Load Scheme Performance
        logger.info("Loading Scheme Performance...")
        df_perf = pd.read_csv(raw_path / "07_scheme_performance.csv")
        df_perf.to_sql("fact_performance", engine, if_exists="replace", index=False)
        
        # 3. Load Transactions
        logger.info("Loading Transactions...")
        df_txn = pd.read_csv(raw_path / "08_investor_transactions.csv")
        df_txn["transaction_date"] = pd.to_datetime(df_txn["transaction_date"])
        df_txn.to_sql("fact_transactions", engine, if_exists="replace", index=False)
        
        # 4. Load NAV History
        logger.info("Loading NAV History...")
        df_nav = pd.read_csv(raw_path / "02_nav_history.csv")
        df_nav["date"] = pd.to_datetime(df_nav["date"])
        df_nav = df_nav.sort_values(by=["amfi_code", "date"])
        df_nav["nav"] = df_nav.groupby("amfi_code")["nav"].ffill()
        df_nav["daily_return_pct"] = df_nav.groupby("amfi_code")["nav"].pct_change() * 100
        df_nav.rename(columns={"date": "nav_date"}, inplace=True)
        df_nav.to_sql("fact_nav", engine, if_exists="replace", index=False)

        # 5. Create Indexes for Performance Optimization
        logger.info("Creating Database Indexes...")
        with engine.connect() as conn:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_dim_fund_amfi ON dim_fund(amfi_code);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fact_perf_amfi ON fact_performance(amfi_code);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fact_perf_return ON fact_performance(return_3yr_pct);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fact_nav_amfi ON fact_nav(amfi_code);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fact_nav_date ON fact_nav(nav_date);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fact_txn_date ON fact_transactions(transaction_date);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fact_txn_type ON fact_transactions(transaction_type);"))
            conn.commit()

        logger.info("ETL Pipeline completed successfully.")
    except Exception as e:
        logger.error(f"ETL Pipeline failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    run_etl()