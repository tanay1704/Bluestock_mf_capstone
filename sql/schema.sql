PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code BIGINT PRIMARY KEY,
    fund_house TEXT NOT NULL,
    scheme_name TEXT NOT NULL,
    category TEXT NOT NULL,
    sub_category TEXT,
    plan TEXT,
    launch_date TEXT,
    benchmark TEXT,
    expense_ratio_pct FLOAT,
    exit_load_pct FLOAT,
    min_sip_amount BIGINT,
    min_lumpsum_amount BIGINT,
    fund_manager TEXT,
    risk_category TEXT,
    sebi_category_code TEXT
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key TEXT PRIMARY KEY,
    full_date DATE NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    day INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_name TEXT NOT NULL,
    is_weekend INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_performance (
    amfi_code BIGINT PRIMARY KEY,
    scheme_name TEXT NOT NULL,
    fund_house TEXT NOT NULL,
    category TEXT NOT NULL,
    plan TEXT,
    return_1yr_pct FLOAT,
    return_3yr_pct FLOAT,
    return_5yr_pct FLOAT,
    benchmark_3yr_pct FLOAT,
    alpha FLOAT,
    beta FLOAT,
    sharpe_ratio FLOAT,
    sortino_ratio FLOAT,
    std_dev_ann_pct FLOAT,
    max_drawdown_pct FLOAT,
    aum_crore BIGINT,
    expense_ratio_pct FLOAT,
    morningstar_rating BIGINT,
    risk_grade TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id TEXT NOT NULL,
    transaction_date DATETIME NOT NULL,
    date_key TEXT NOT NULL,
    amfi_code BIGINT NOT NULL,
    transaction_type TEXT NOT NULL CHECK(transaction_type IN ('SIP', 'Lumpsum', 'Redemption')),
    amount_inr BIGINT NOT NULL,
    state TEXT,
    city TEXT,
    city_tier TEXT,
    age_group TEXT,
    gender TEXT,
    annual_income_lakh FLOAT,
    payment_mode TEXT,
    kyc_status TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
);

CREATE TABLE IF NOT EXISTS fact_nav (
    amfi_code BIGINT NOT NULL,
    nav_date DATE NOT NULL,
    date_key TEXT NOT NULL,
    nav FLOAT NOT NULL,
    daily_return_pct FLOAT,
    PRIMARY KEY (amfi_code, nav_date),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
);

CREATE TABLE IF NOT EXISTS fact_aum (
    aum_id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_date DATE NOT NULL,
    date_key TEXT NOT NULL,
    fund_house TEXT NOT NULL,
    aum_lakh_crore FLOAT NOT NULL,
    aum_crore BIGINT NOT NULL,
    num_schemes INTEGER NOT NULL,
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
);

CREATE TABLE IF NOT EXISTS clustered_investors (
    investor_id TEXT PRIMARY KEY,
    total_invested FLOAT NOT NULL,
    txn_count INTEGER NOT NULL,
    annual_income FLOAT NOT NULL,
    cluster INTEGER NOT NULL CHECK(cluster IN (0, 1, 2)),
    cluster_label TEXT
);

CREATE INDEX IF NOT EXISTS idx_dim_fund_amfi ON dim_fund(amfi_code);
CREATE INDEX IF NOT EXISTS idx_dim_date_key ON dim_date(date_key);
CREATE INDEX IF NOT EXISTS idx_fact_perf_amfi ON fact_performance(amfi_code);
CREATE INDEX IF NOT EXISTS idx_fact_perf_return ON fact_performance(return_3yr_pct);
CREATE INDEX IF NOT EXISTS idx_fact_nav_amfi ON fact_nav(amfi_code);
CREATE INDEX IF NOT EXISTS idx_fact_nav_date ON fact_nav(nav_date);
CREATE INDEX IF NOT EXISTS idx_fact_txn_amfi ON fact_transactions(amfi_code);
CREATE INDEX IF NOT EXISTS idx_fact_txn_investor ON fact_transactions(investor_id);
CREATE INDEX IF NOT EXISTS idx_fact_txn_date ON fact_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_fact_txn_type ON fact_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_fact_aum_date ON fact_aum(report_date);
CREATE INDEX IF NOT EXISTS idx_fact_aum_fh ON fact_aum(fund_house);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    is_verified INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS login_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    ip_address TEXT NOT NULL,
    attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS password_resets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_login_attempts_email_time ON login_attempts(email, attempt_time);
CREATE INDEX IF NOT EXISTS idx_login_attempts_ip_time ON login_attempts(ip_address, attempt_time);
CREATE INDEX IF NOT EXISTS idx_password_resets_token ON password_resets(token_hash);
