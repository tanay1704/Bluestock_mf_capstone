-- ==============================================================================
-- BLUESTOCK MUTUAL FUND ANALYTICS PLATFORM
-- Database Schema Definition (Star Schema Architecture)
-- Target RDBMS: SQLite 3 / PostgreSQL Compatible
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Dimension Table: Fund Master (dim_fund)
-- Grain: One record per mutual fund scheme (amfi_code PK)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code               BIGINT PRIMARY KEY,
    fund_house              TEXT NOT NULL,
    scheme_name             TEXT NOT NULL,
    category                TEXT NOT NULL,
    sub_category            TEXT,
    plan                    TEXT,
    launch_date             TEXT,
    benchmark               TEXT,
    expense_ratio_pct       FLOAT,
    exit_load_pct           FLOAT,
    min_sip_amount          BIGINT,
    min_lumpsum_amount      BIGINT,
    fund_manager            TEXT,
    risk_category           TEXT,
    sebi_category_code      TEXT
);

-- ------------------------------------------------------------------------------
-- Fact Table: Scheme Performance (fact_performance)
-- Grain: One record per scheme summary metrics (amfi_code FK)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_performance (
    amfi_code               BIGINT PRIMARY KEY,
    scheme_name             TEXT NOT NULL,
    fund_house              TEXT NOT NULL,
    category                TEXT NOT NULL,
    plan                    TEXT,
    return_1yr_pct          FLOAT,
    return_3yr_pct          FLOAT,
    return_5yr_pct          FLOAT,
    benchmark_3yr_pct       FLOAT,
    alpha                   FLOAT,
    beta                    FLOAT,
    sharpe_ratio            FLOAT,
    sortino_ratio           FLOAT,
    std_dev_ann_pct         FLOAT,
    max_drawdown_pct        FLOAT,
    aum_crore               BIGINT,
    expense_ratio_pct       FLOAT,
    morningstar_rating      BIGINT,
    risk_grade              TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

-- ------------------------------------------------------------------------------
-- Fact Table: Investor Transactions (fact_transactions)
-- Grain: One record per investor transaction (SIP, Lumpsum, Redemption)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_transactions (
    investor_id             TEXT NOT NULL,
    transaction_date        DATETIME NOT NULL,
    amfi_code               BIGINT NOT NULL,
    transaction_type        TEXT NOT NULL CHECK(transaction_type IN ('SIP', 'Lumpsum', 'Redemption')),
    amount_inr              BIGINT NOT NULL,
    state                   TEXT,
    city                    TEXT,
    city_tier               TEXT,
    age_group               TEXT,
    gender                  TEXT,
    annual_income_lakh      FLOAT,
    payment_mode            TEXT,
    kyc_status              TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

-- ------------------------------------------------------------------------------
-- Fact Table: Historical Net Asset Value (fact_nav)
-- Grain: One record per scheme per trading day
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_nav (
    amfi_code               BIGINT NOT NULL,
    nav_date                DATETIME NOT NULL,
    nav                     FLOAT NOT NULL,
    daily_return_pct        FLOAT,
    PRIMARY KEY (amfi_code, nav_date),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

-- ------------------------------------------------------------------------------
-- Dimension Table: Machine Learning Investor Clusters (clustered_investors)
-- Grain: One record per distinct investor (investor_id PK)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clustered_investors (
    investor_id             TEXT PRIMARY KEY,
    total_invested          FLOAT NOT NULL,
    txn_count               INTEGER NOT NULL,
    annual_income           FLOAT NOT NULL,
    cluster                 INTEGER NOT NULL CHECK(cluster IN (0, 1, 2))
);

-- ------------------------------------------------------------------------------
-- Performance Indexes for OLAP Query Optimization
-- ------------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_dim_fund_amfi ON dim_fund(amfi_code);
CREATE INDEX IF NOT EXISTS idx_fact_perf_amfi ON fact_performance(amfi_code);
CREATE INDEX IF NOT EXISTS idx_fact_perf_return ON fact_performance(return_3yr_pct);
CREATE INDEX IF NOT EXISTS idx_fact_nav_amfi ON fact_nav(amfi_code);
CREATE INDEX IF NOT EXISTS idx_fact_nav_date ON fact_nav(nav_date);
CREATE INDEX IF NOT EXISTS idx_fact_txn_amfi ON fact_transactions(amfi_code);
CREATE INDEX IF NOT EXISTS idx_fact_txn_investor ON fact_transactions(investor_id);
CREATE INDEX IF NOT EXISTS idx_fact_txn_date ON fact_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_fact_txn_type ON fact_transactions(transaction_type);
