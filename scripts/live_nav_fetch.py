import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import requests
import schedule
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('LiveNAV_Fetcher')

def get_database_engine():
    base_dir = Path(__file__).resolve().parent.parent
    default_db_path = base_dir / "data" / "db" / "bluestock_mf.db"
    db_url = os.environ.get('DATABASE_URL', f"sqlite:///{default_db_path.as_posix()}")
    if db_url.startswith('sqlite:///db/'):
        db_url = f"sqlite:///{default_db_path.as_posix()}"
    return create_engine(db_url)

def fetch_latest_nav_from_mfapi(amfi_code: int, max_retries: int = 3, timeout_sec: int = 10) -> Optional[Dict[str, Any]]:
    base_url = os.environ.get("MFAPI_BASE_URL", "https://api.mfapi.in/mf").rstrip('/')
    url = f"{base_url}/{amfi_code}"
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=timeout_sec)
            if response.status_code == 200:
                payload = response.json()
                data_points = payload.get("data", [])
                if data_points:
                    latest = data_points[0]
                    raw_date = latest.get("date")
                    parsed_date = datetime.strptime(raw_date, "%d-%m-%Y").strftime("%Y-%m-%d")
                    nav_value = float(latest.get("nav"))
                    return {
                        "amfi_code": amfi_code,
                        "nav_date": parsed_date,
                        "date_key": parsed_date,
                        "nav": nav_value
                    }
            elif response.status_code in (429, 500, 502, 503, 504):
                wait_time = (2 ** attempt) * 0.5
                time.sleep(wait_time)
                continue
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 0.5
                time.sleep(wait_time)
                continue
            logger.warning(f"Error fetching NAV for scheme {amfi_code}: {e}")
        except Exception as e:
            logger.warning(f"Error parsing NAV for scheme {amfi_code}: {e}")
            break
    return None

def fetch_and_update_all_navs(sample_limit: Optional[int] = None) -> int:
    engine = get_database_engine()
    with engine.connect() as conn:
        df_schemes = pd.read_sql("SELECT DISTINCT amfi_code FROM dim_fund", conn)
    
    amfi_codes = df_schemes['amfi_code'].tolist()
    if sample_limit:
        amfi_codes = amfi_codes[:sample_limit]
        
    records_added = 0
    with engine.connect() as conn:
        for code in amfi_codes:
            record = fetch_latest_nav_from_mfapi(code)
            if record:
                stmt = text("""
                    INSERT OR IGNORE INTO fact_nav (amfi_code, nav_date, date_key, nav, daily_return_pct)
                    VALUES (:amfi_code, :nav_date, :date_key, :nav, 0.0)
                """)
                conn.execute(stmt, record)
                records_added += 1
        conn.commit()
        
    logger.info(f"Live NAV ingestion complete. Checked {len(amfi_codes)} schemes, processed {records_added} updates.")
    return records_added

def run_scheduler_loop() -> None:
    logger.info("Initializing Live NAV scheduler for Weekdays at 20:00 IST...")
    schedule.every().monday.at("20:00").do(fetch_and_update_all_navs)
    schedule.every().tuesday.at("20:00").do(fetch_and_update_all_navs)
    schedule.every().wednesday.at("20:00").do(fetch_and_update_all_navs)
    schedule.every().thursday.at("20:00").do(fetch_and_update_all_navs)
    schedule.every().friday.at("20:00").do(fetch_and_update_all_navs)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        run_scheduler_loop()
    else:
        logger.info("Running single live NAV synchronization batch...")
        fetch_and_update_all_navs(sample_limit=5)

