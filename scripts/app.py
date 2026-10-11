import os
import logging
from typing import Tuple, List, Dict, Any
from functools import lru_cache
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure enterprise logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Bluestock_API')

app = Flask(__name__)
# Enable CORS for the entire API, allowing all origins (can be restricted for production)
CORS(app)

# Configure Database Connection using SQLAlchemy (Connection Pooling)
default_db_path = os.path.join(os.path.dirname(__file__), '../db/bluestock_mf.db')
db_url = os.environ.get('DATABASE_URL', f"sqlite:///{default_db_path}")

if db_url.startswith('sqlite:///db/'):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_url = f"sqlite:///{os.path.join(base_dir, 'db', 'bluestock_mf.db')}"

try:
    engine = create_engine(db_url, pool_pre_ping=True)
except Exception as e:
    logger.error(f"Failed to initialize database engine: {e}")
    raise

@app.errorhandler(Exception)
def handle_exception(e: Exception) -> Tuple[Response, int]:
    """
    Global exception handler for all uncaught errors.
    
    Args:
        e (Exception): The uncaught exception.
        
    Returns:
        Tuple[Response, int]: A JSON response containing error details and a 500 HTTP status code.
    """
    logger.error(f"Unhandled Exception: {str(e)}", exc_info=True)
    return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check() -> Tuple[Response, int]:
    """
    API Health Check Endpoint.
    
    Returns:
        Tuple[Response, int]: A JSON response indicating API and database health status.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        logger.error("Health check failed", exc_info=True)
        return jsonify({"status": "unhealthy", "error": str(e)}), 503

@lru_cache(maxsize=32)
def _fetch_top_funds(limit: int) -> List[Dict[str, Any]]:
    """Helper function to fetch and cache top funds data."""
    query = text("""
        SELECT scheme_name, category, return_3yr_pct, sharpe_ratio 
        FROM fact_performance 
        ORDER BY return_3yr_pct DESC 
        LIMIT :limit
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"limit": limit})
    return df.to_dict(orient='records')

@app.route('/api/top-funds', methods=['GET'])
def get_top_funds() -> Tuple[Response, int]:
    """
    Returns the top performing funds based on 3-year returns.
    
    Query Parameters:
        limit (int): The number of top funds to retrieve. Defaults to 5.
        
    Returns:
        Tuple[Response, int]: A JSON list of dictionaries containing fund performance metrics.
    """
    limit: int = request.args.get('limit', default=5, type=int)
    try:
        data = _fetch_top_funds(limit)
        return jsonify(data), 200
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_top_funds: {e}")
        return jsonify({"error": "Database error"}), 500

@lru_cache(maxsize=1)
def _fetch_investor_stats() -> List[Dict[str, Any]]:
    """Helper function to fetch and cache investor stats data."""
    query = text("""
        SELECT transaction_type, SUM(amount_inr) as total_volume, COUNT(*) as transaction_count 
        FROM fact_transactions 
        GROUP BY transaction_type
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df.to_dict(orient='records')

@app.route('/api/investor-stats', methods=['GET'])
def get_investor_stats() -> Tuple[Response, int]:
    """
    Returns the total investment volume split by transaction type (SIP vs Lumpsum).
    
    Returns:
        Tuple[Response, int]: A JSON list of dictionaries containing aggregated investment stats.
    """
    try:
        data = _fetch_investor_stats()
        return jsonify(data), 200
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_investor_stats: {e}")
        return jsonify({"error": "Database error"}), 500

if __name__ == '__main__':
    logger.info("Starting Bluestock Fintech API with CORS and Caching enabled...")
    app.run(debug=True, port=5000)
