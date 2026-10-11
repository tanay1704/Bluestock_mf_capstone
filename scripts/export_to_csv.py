import sqlite3
import pandas as pd
from pathlib import Path

def export_data_to_csv():
    """
    Connects to the SQLite database and exports the fact and dimension 
    tables to the data/clean directory as CSV files.
    """
    BASE_DIR = Path(__file__).resolve().parent.parent
    db_path = BASE_DIR / "db" / "bluestock_mf.db"
    export_dir = BASE_DIR / "data" / "clean"

    export_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)

    tables = ["dim_fund", "fact_performance", "fact_transactions", "fact_nav"]

    for table in tables:
        df = pd.read_sql(f"SELECT * FROM {table}", conn)
        export_path = export_dir / f"{table}.csv"
        df.to_csv(export_path, index=False)

    conn.close()

if __name__ == "__main__":
    export_data_to_csv()
