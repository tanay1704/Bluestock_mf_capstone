import os
import logging
from typing import Tuple, Optional
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging for the dashboard
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('Dashboard')

# --- PAGE CONFIG & CUSTOM CSS ---
st.set_page_config(page_title="Bluestock MF Analytics", page_icon="📈", layout="wide")

# Custom CSS for rich aesthetics
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        --primary: #60A5FA;
        --primary-glow: rgba(96, 165, 250, 0.4);
        --bg-base: #0B0F19;
        --bg-glass: rgba(15, 23, 42, 0.65);
        --border-glass: rgba(255, 255, 255, 0.08);
        --text-main: #F8FAFC;
        --text-muted: #94A3B8;
    }

    /* Overall App Background with subtle gradient */
    .stApp {
        background: radial-gradient(circle at 15% 50%, rgba(30, 58, 138, 0.15), transparent 25%),
                    radial-gradient(circle at 85% 30%, rgba(56, 189, 248, 0.1), transparent 25%);
        background-color: var(--bg-base);
        color: var(--text-main);
        font-family: 'Inter', sans-serif;
    }

    /* Typography Overrides */
    h1, h2, h3, h4, h5, h6, p, span {
        font-family: 'Inter', sans-serif !important;
        color: var(--text-main) !important;
    }
    
    h1 {
        font-weight: 700 !important;
        background: -webkit-linear-gradient(45deg, #F8FAFC, #93C5FD);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }

    /* Premium Glassmorphism Metric Cards */
    .metric-card {
        background: var(--bg-glass);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid var(--border-glass);
        border-radius: 16px;
        padding: 1.5rem 2rem;
        text-align: center;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        position: relative;
        overflow: hidden;
    }
    
    /* Hover glow effect */
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: -100%;
        width: 50%; height: 100%;
        background: linear-gradient(to right, transparent, rgba(255, 255, 255, 0.03), transparent);
        transform: skewX(-25deg);
        transition: left 0.5s;
    }

    .metric-card:hover::before {
        left: 150%;
    }

    .metric-card:hover {
        transform: translateY(-5px);
        border-color: rgba(96, 165, 250, 0.3);
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2), 0 0 15px var(--primary-glow);
    }
    
    .metric-value {
        font-size: 2.25rem;
        font-weight: 700;
        color: var(--primary);
        margin: 12px 0;
        letter-spacing: -0.02em;
    }
    
    .metric-label {
        font-size: 0.95rem;
        font-weight: 500;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Streamlit Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        border-bottom: 1px solid var(--border-glass);
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border-radius: 4px 4px 0 0;
        border: none !important;
        color: var(--text-muted) !important;
        padding-top: 1rem;
        padding-bottom: 1rem;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        color: var(--primary) !important;
        border-bottom: 2px solid var(--primary) !important;
        background-color: rgba(96, 165, 250, 0.05) !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.8) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid var(--border-glass);
    }
</style>
""", unsafe_allow_html=True)

st.title("📈 Bluestock Fintech: Enterprise Analytics")
st.markdown("Enterprise-grade Mutual Fund Intelligence and AI-powered Insights.")

# --- LOAD DATA (CACHED) ---
@st.cache_data(ttl=3600)
def load_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Loads data using SQLAlchemy for better performance and type safety.
    Caches the results to prevent redundant database hits.
    
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]: 
        Dataframes for fund master, performance, transactions, NAV history, and merged view.
        
    Raises:
        Exception: If database connection or query execution fails.
    """
    try:
        BASE_DIR = Path(__file__).resolve().parent
        default_db_path = BASE_DIR / "db" / "bluestock_mf.db"
        db_url = os.environ.get('DATABASE_URL', f"sqlite:///{default_db_path}")
        
        # Ensure absolute path for sqlite if using relative in .env
        if db_url.startswith('sqlite:///db/'):
            db_url = f"sqlite:///{BASE_DIR / 'db' / 'bluestock_mf.db'}"

        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            df_fund = pd.read_sql("SELECT * FROM dim_fund", conn)
            df_perf = pd.read_sql("SELECT * FROM fact_performance", conn)
            df_txn = pd.read_sql("SELECT * FROM fact_transactions", conn)
            df_nav = pd.read_sql("SELECT * FROM fact_nav", conn)
            
            # Joined view for dashboard
            query = """
                SELECT p.*, f.category, f.scheme_name, f.fund_house 
                FROM fact_performance p
                JOIN dim_fund f ON p.amfi_code = f.amfi_code
            """
            df_merged = pd.read_sql(query, conn)
        
        df_merged = df_merged.loc[:, ~df_merged.columns.duplicated()]
        df_txn['transaction_date'] = pd.to_datetime(df_txn['transaction_date'])
        df_nav['nav_date'] = pd.to_datetime(df_nav['nav_date'])
        
        logger.info("Successfully loaded database tables into pandas dataframes.")
        return df_fund, df_perf, df_txn, df_nav, df_merged
    except Exception as e:
        logger.error(f"Failed to load data: {e}", exc_info=True)
        raise

try:
    df_fund, df_perf, df_txn, df_nav, df_merged = load_data()
except Exception as e:
    st.error(f"Failed to load data from database: {e}")
    st.stop()

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filter Controls")
selected_category = st.sidebar.multiselect(
    "Fund Category",
    options=df_merged["category"].unique(),
    default=df_merged["category"].unique()
)

top_fund_houses = df_merged["fund_house"].value_counts().nlargest(5).index.tolist()
selected_fund_house = st.sidebar.multiselect(
    "Fund House",
    options=df_merged["fund_house"].unique(),
    default=top_fund_houses
)

filtered_df = df_merged[
    (df_merged["category"].isin(selected_category)) & 
    (df_merged["fund_house"].isin(selected_fund_house))
]

# --- MODULAR TAB FUNCTIONS ---

def render_performance_tab() -> None:
    """Renders the Fund Performance Analytics tab."""
    st.header("📊 Fund Performance Analytics")
    
    if filtered_df.empty:
        st.warning("No data available for the selected filters.")
        return
        
    col1, col2, col3 = st.columns(3)
    avg_return = filtered_df["return_3yr_pct"].mean()
    top_fund = filtered_df.loc[filtered_df["return_3yr_pct"].idxmax()]["scheme_name"]
    avg_sharpe = filtered_df["sharpe_ratio"].mean()
    
    col1.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Avg 3-Year Return</div>
            <div class="metric-value">{avg_return:.2f}%</div>
        </div>
    """, unsafe_allow_html=True)
    
    col2.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Top Performing Fund</div>
            <div class="metric-value" style="font-size: 1.2rem; padding: 15px 0;">{top_fund}</div>
        </div>
    """, unsafe_allow_html=True)
    
    col3.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Avg Sharpe Ratio</div>
            <div class="metric-value">{avg_sharpe:.2f}</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.subheader("Average 3-Year Return by Fund House")
        perf_summary = filtered_df.groupby("fund_house")["return_3yr_pct"].mean().sort_values(ascending=False)
        st.bar_chart(perf_summary)
        
    with col_chart2:
        st.subheader("Risk vs Return Analysis")
        st.scatter_chart(
            filtered_df, x="std_dev_ann_pct", y="return_3yr_pct",
            color="category", size="aum_crore"
        )

def render_nav_tab() -> None:
    """Renders the NAV Trends tab."""
    st.header("📉 Net Asset Value (NAV) Trends")
    if filtered_df.empty:
        st.warning("No data available for the selected filters.")
        return
        
    st.markdown("Historical NAV tracking for the top 5 funds within the current selection.")
    top_funds = filtered_df.nlargest(5, 'return_3yr_pct')['amfi_code'].tolist()
    nav_filtered = df_nav[df_nav['amfi_code'].isin(top_funds)]
    
    nav_display = pd.merge(nav_filtered, df_fund[['amfi_code', 'scheme_name']], on='amfi_code')
    nav_pivot = nav_display.pivot(index="nav_date", columns="scheme_name", values="nav").dropna()
    
    st.line_chart(nav_pivot, use_container_width=True)

def render_investor_tab() -> None:
    """Renders the Investor Analytics & Volume tab."""
    st.header("💰 Investor Analytics & Volume")
    
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.subheader("Transaction Volume (SIP vs Lumpsum)")
        txn_summary = df_txn.groupby("transaction_type")["amount_inr"].sum()
        st.bar_chart(txn_summary)
        
    with col_chart2:
        st.subheader("Monthly Investment Trends")
        df_txn['month_year'] = df_txn['transaction_date'].dt.to_period('M').astype(str)
        monthly_vol = df_txn.groupby(['month_year', 'transaction_type'])['amount_inr'].sum().unstack()
        st.line_chart(monthly_vol)

def render_chat_tab() -> None:
    """Renders the AI Data Analyst (Gemini) chat tab."""
    st.header("🤖 AI Data Analyst (Gemini)")
    st.markdown("Ask questions about the mutual fund data in natural language.")
    
    api_key: Optional[str] = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        st.info("Please set the GEMINI_API_KEY environment variable in your .env file to enable the AI chat.")
        return
        
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        context = f"""
        You are an AI assistant for a mutual fund analytics platform.
        Here is a summary of the current data:
        - Total Funds: {len(df_fund)}
        - Average 3-Year Return: {df_perf['return_3yr_pct'].mean():.2f}%
        - Top Categories: {', '.join(df_fund['category'].value_counts().head(3).index.tolist())}
        Answer the user's questions strictly based on this context. Keep it concise.
        """
        
        if "messages" not in st.session_state:
            st.session_state.messages = []
            
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
        if prompt := st.chat_input("Ask a question about the mutual funds..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
                
            with st.chat_message("assistant"):
                response = model.generate_content(f"{context}\nUser: {prompt}")
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
    except Exception as e:
        logger.error(f"Chat API error: {e}")
        st.error(f"Error communicating with AI: {e}")

# --- TAB NAVIGATION ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Performance", 
    "📉 NAV Trends", 
    "💰 Investor Analytics",
    "🤖 Ask AI"
])

with tab1:
    render_performance_tab()
with tab2:
    render_nav_tab()
with tab3:
    render_investor_tab()
with tab4:
    render_chat_tab()
