<div align="center">
  <h1>📈 Bluestock Fintech: Mutual Fund Analytics Platform</h1>
  <p><strong>Enterprise Data Engineering, Star Schema Warehouse, Machine Learning & Business Intelligence Ecosystem</strong></p>

  <p>
    <img src="https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg" alt="Python Versions">
    <img src="https://img.shields.io/badge/Database-SQLite3%20(Star%20Schema)-003B57.svg" alt="SQLite">
    <img src="https://img.shields.io/badge/Machine%20Learning-Scikit--Learn%20K--Means-orange.svg" alt="Scikit-Learn">
    <img src="https://img.shields.io/badge/Business%20Intelligence-Power%20BI-F2C811.svg" alt="Power BI">
    <img src="https://img.shields.io/badge/Analytics-MPT%20%7C%20Monte%20Carlo%20%7C%20VaR-darkgreen.svg" alt="Quantitative Finance">
  </p>
</div>

---

## 1. Executive Summary & Architecture Overview

The **Bluestock Mutual Fund Analytics Platform** is an institutional data engineering, quantitative financial modeling, and business intelligence ecosystem. Designed for scale and precision, the platform ingests 10 operational CSV feeds across 40 schemes, 64,320 calendar days of Net Asset Value (NAV) trajectories, and 32,778 retail transactions.

It enforces strict financial audit reconciliation, houses a normalized SQLite Star Schema relational warehouse, applies unsupervised machine learning (K-Means) for behavioral investor segmentation, runs trading-day annualized risk-adjusted metrics, executes 10,000-path Monte Carlo simulations and Markowitz portfolio optimizations, and delivers insights via an executive 4-page Power BI dashboard.

### End-to-End Pipeline Architecture

```mermaid
flowchart TD
    subgraph Tier1 ["1. Data Ingestion & Live Streams"]
        RAW["Raw Operational CSVs<br/>(data/raw/*.csv)"]
        LIVE["AMFI Live NAV Fetcher<br/>(scripts/live_nav_fetch.py)"]
    end

    subgraph Tier2 ["2. Data Engineering & Star Schema Storage"]
        ETL["Automated ETL Pipeline<br/>(scripts/etl_pipeline.py)"]
        DB[("SQLite Star Schema Warehouse<br/>(data/db/bluestock_mf.db)")]
        PROC["Clean Dimensional Datasets<br/>(data/processed/*.csv)"]
    end

    subgraph Tier3 ["3. Quantitative Modeling & Machine Learning"]
        METRICS["Performance Analytics Engine<br/>(scripts/compute_metrics.py)"]
        RECOMMEND["Multi-Factor Recommender & VaR<br/>(scripts/recommender.py)"]
    end

    subgraph Tier4 ["4. Executive Presentation & Dashboards"]
        PBI["Power BI Executive Dashboard<br/>(dashboard/bluestock_mf.pbix)"]
        REPORTS["Final Reports & Documentation<br/>(reports/)"]
    end

    RAW --> ETL
    LIVE --> DB
    ETL --> DB
    ETL --> PROC
    PROC --> METRICS
    PROC --> RECOMMEND
    PROC --> PBI
    METRICS --> REPORTS
    RECOMMEND --> REPORTS
```

---

## 2. Evaluation Rubric & Deliverables Alignment

The platform satisfies all primary deliverables (**D1 through D7**) and core quantitative extensions:

| Deliverable ID | Capstone Evaluation Rubric Requirement | Platform Implementation & Verified Artifact | Verification Command / Target Location |
| :--- | :--- | :--- | :--- |
| **D1** | Production Python ETL Pipeline with Data Validation | [`scripts/etl_pipeline.py`](scripts/etl_pipeline.py): Ingestion of 10 feeds, holiday imputation via calendar reindexing, transaction/KYC cleaning, boundary assertions. | `python scripts/etl_pipeline.py` |
| **D2** | Relational Star Schema Data Warehouse & SQL Queries | [`sql/schema.sql`](sql/schema.sql) & [`sql/queries.sql`](sql/queries.sql): Relational tables (`dim_fund`, `dim_date`, `fact_nav`, `fact_transactions`, `fact_performance`, `fact_aum`), indexes, 10 analytical queries. | SQLite queries in `sql/queries.sql` |
| **D3** | Ingestion, Cleaning, and Exploratory Analysis Notebooks | [`notebooks/01_data_ingestion.ipynb`](notebooks/01_data_ingestion.ipynb), [`notebooks/02_data_cleaning.ipynb`](notebooks/02_data_cleaning.ipynb), [`notebooks/03_eda_analysis.ipynb`](notebooks/03_eda_analysis.ipynb): Schema audits, distribution charts, SIP trajectories. | Verified execution with saved in-place outputs. |
| **D4** | Quantitative Performance Metrics Engine | [`scripts/compute_metrics.py`](scripts/compute_metrics.py) & [`notebooks/04_performance_analytics.ipynb`](notebooks/04_performance_analytics.ipynb): CAGR, Volatility, Sharpe, Sortino, Alpha, Beta, Max Drawdown (252-day basis). | `python scripts/compute_metrics.py` |
| **D5** | Power BI Executive Dashboard & UI Alignment | [`dashboard/bluestock_mf.pbix`](dashboard/bluestock_mf.pbix): 4-page dashboard, single-direction filters, star schema relationships, verified ₹3.52 Bn KPI volume card. | Screenshots in [`dashboard/screenshot/`](dashboard/screenshot/) |
| **D6** | Advanced Analytics, Cohort Retention & Recommender | [`scripts/recommender.py`](scripts/recommender.py) & [`notebooks/05_advanced_analytics.ipynb`](notebooks/05_advanced_analytics.ipynb): Historical/Parametric VaR (95%/99%), retention matrices, K-Means personas. | `python scripts/recommender.py` |
| **D7** | Executive Technical Documentation & Reports | [`reports/Final_Report.pdf`](reports/Final_Report.pdf), [`reports/Presentation.pptx`](reports/Presentation.pptx), [`reports/data_dictionary.md`](reports/data_dictionary.md), and [`README.md`](README.md). | Complete artifact verification in `reports/` |
| **B1** | Automated Live NAV Data Ingestion | [`scripts/live_nav_fetch.py`](scripts/live_nav_fetch.py): Real-time AMFI API ingestion (`https://api.mfapi.in/mf`) with weekday 20:00 schedule loop. | `python scripts/live_nav_fetch.py` |
| **B3** | Five-Year 10,000-Path Monte Carlo Simulation | [`scripts/compute_metrics.py`](scripts/compute_metrics.py) & [`notebooks/05_advanced_analytics.ipynb`](notebooks/05_advanced_analytics.ipynb): Geometric Brownian Motion with 5th, 50th, and 95th percentiles. | Embedded in notebook & metrics engine. |
| **B4** | Five-Fund Markowitz Modern Portfolio Theory Optimization | [`scripts/compute_metrics.py`](scripts/compute_metrics.py) & [`notebooks/05_advanced_analytics.ipynb`](notebooks/05_advanced_analytics.ipynb): SLSQP optimization solving for Maximum Sharpe and Minimum Volatility. | Embedded in notebook & metrics engine. |

---

## 3. Repository Directory Structure

```text
bluestock_mf_capstone/
├── data/
│   ├── raw/                  (10 original CSVs)
│   ├── processed/            (cleaned CSVs)
│   └── db/                   (bluestock_mf.db - ignored by Git)
├── notebooks/
│   ├── 01_data_ingestion.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_eda_analysis.ipynb
│   ├── 04_performance_analytics.ipynb
│   └── 05_advanced_analytics.ipynb
├── scripts/
│   ├── etl_pipeline.py
│   ├── live_nav_fetch.py
│   ├── compute_metrics.py
│   └── recommender.py
├── sql/
│   ├── schema.sql
│   └── queries.sql
├── dashboard/
│   ├── bluestock_mf.pbix
│   └── screenshot/           (p1, p2, p3, p4 images for README)
├── reports/
│   ├── Final_Report.pdf
│   ├── Presentation.pptx
│   └── data_dictionary.md
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 4. Financial Audit & Mathematical Reconciliation

Zero-tolerance reconciliation between operational raw transaction feeds, SQLite warehouse facts, and Power BI visual aggregations:

| Financial Metric | Analytical Formulation | Reconciled Value | Financial Interpretation |
| :--- | :--- | :--- | :--- |
| **Gross Platform Turnover** | `SUM(amount_inr)` | **₹3,521,580,430** | Exactly ₹3.52 Billion across 32,778 transactions. |
| **Lumpsum Volume** | `SUM(amount_inr) WHERE type='Lumpsum'` | **₹2,059,821,448** | 8,095 transactions; 58.5% gross platform volume. |
| **SIP Volume** | `SUM(amount_inr) WHERE type='SIP'` | **₹217,233,491** | 19,716 transactions; disciplined retail capital base. |
| **Redemption Outflows** | `SUM(amount_inr) WHERE type='Redemption'` | **₹1,244,525,491** | 4,967 transactions; 35.3% gross outflow rate. |
| **Net Inflow Capital** | `(Lumpsum + SIP) - Redemption` | **₹1,032,529,448** | **₹1.03 Bn net asset inflow** expanded on platform. |
| **Unique Investor Base** | `COUNT(DISTINCT investor_id)` | **5,000** | 100% referential integrity with zero orphan records. |

### Unit Disambiguation Architecture
- **Scheme-Level AUM (`aum_crore`):** Quantified in Crores ($10^7$ INR). Applied in `dim_fund` and `fact_performance`.
- **AMC / Macro-Level AUM (`aum_lakh_crore`):** Quantified in Lakh Crores ($10^{12}$ INR). Applied in `03_aum_by_fund_house.csv` and `04_monthly_sip_inflows.csv`.

---

## 5. Key Quantitative Findings & Modeling Insights

### 1. Risk-Adjusted Return Outliers (252 Trading-Day Convention)
- **Top 3-Year CAGR Performers:** Small Cap schemes consistently generated >25% annualized returns, led by *SBI Small Cap Fund* (31.2%) and *Nippon India Small Cap Fund* (29.8%).
- **Superior Sharpe Ratios:** Flexi Cap and Large & Mid Cap categories delivered superior risk-adjusted profiles (Sharpe ratios > 1.45) with lower downside volatility (Sortino ratios > 1.80).
- **Maximum Drawdowns:** Market correction cycles exposed small-cap portfolios to peak drawdowns of -28.4%, while balanced hybrid schemes constrained drawdown risk within -12.1%.

### 2. Behavioral Investor Personas (K-Means Clustering, $k=3$)
- **Cluster 0: Moderate Retail (39.2% of base):**
  - Average Invested Capital: ₹11,72,193 | Average Transaction Count: 9.7 | Income: ~₹15.2 Lakhs.
  - Persona Profile: Disciplined SIP investors with recurring contributions and high platform retention.
- **Cluster 1: Affluent HNI (42.9% of base):**
  - Average Invested Capital: ₹3,28,753 | Average Transaction Count: 3.9 | Income: ~₹24.8 Lakhs.
  - Persona Profile: Large opportunistic lumpsum allocations into aggressive equity and thematic funds.
- **Cluster 2: Emerging Youth (17.9% of base):**
  - Average Invested Capital: ₹5,81,665 | Average Transaction Count: 6.1 | Income: ~₹9.8 Lakhs.
  - Persona Profile: Young digital adopters with high UPI utilization seeking digital equity entry points.

### 3. Modern Portfolio Theory (MPT) & Monte Carlo Simulation
- **Markowitz Efficient Frontier:** Allocating capital across 5 non-correlated funds (Large Cap 30%, Flexi Cap 25%, Mid Cap 20%, Hybrid 15%, Debt 10%) increased Sharpe ratio by +34 bps over single-scheme holding.
- **Monte Carlo 10,000-Path NAV Simulation:** Over a 5-year investment horizon ($T=5$, 1,260 trading days), the 90% confidence envelope spans ₹382.40 (5th percentile downside floor) to ₹1,148.90 (95th percentile bull trajectory), with median terminal value of ₹613.50.

---

## 6. Power BI Executive Dashboard Walkthrough

The production dashboard ([dashboard/bluestock_mf.pbix](dashboard/bluestock_mf.pbix)) provides four analytical reporting views with single-direction filtering and star schema relationships:

### Page 1: Executive Overview & Fund Performance
*High-level AUM benchmarks, 3-year annualized return distributions across fund categories, and top-performing schemes.*  
*Interactive Slicers:* Mutual Fund Category (`category`), Fund House (`fund_house`).  
![Page 1: Executive Overview](dashboard/screenshot/p1.png)

---

### Page 2: Risk-Return Profile & Historical NAV Trends
*Bivariate Sharpe ratio vs. annualized volatility scatter plots, multi-asset historical NAV time series, and maximum drawdown risk grading.*  
*Interactive Slicers:* Mutual Fund Scheme (`scheme_name`), SEBI Risk Category (`risk_category`).  
![Page 2: Risk-Return & NAV Analytics](dashboard/screenshot/p2.png)

---

### Page 3: Transaction Dynamics & Cash Flow Analysis
*Granular breakdown uncovering the platform's capital structure: **₹2.06 Bn Lumpsum (58.5%)** versus **₹0.22 Bn SIP (6.2%)**, monthly inflow volumes, and redemption turnover.*  
*Interactive Slicers:* Transaction Type (`transaction_type`), Investor City Tier (`city_tier`).  
![Page 3: Transaction Dynamics](dashboard/screenshot/p3.png)

---

### Page 4: AI Investor Segmentation & Persona Scorecards
*Unsupervised K-Means clustering ($k=3$) surfacing behavioral investor segments—**Moderate Retail**, **Affluent HNI**, and **Emerging Youth**—with demographic distributions and targeted marketing playbooks.*  
*Interactive Slicers:* Investor Persona Cluster (`cluster_label`), KYC Verification Status (`kyc_status`).  
![Page 4: AI Persona Analytics](dashboard/screenshot/p4.png)

---

## 7. End-to-End Execution Guide

Follow these verified terminal instructions to run each component of the platform:

### 1. Environment Setup
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Execute Data Engineering Pipeline (D1 & D2)
```bash
python scripts/etl_pipeline.py
```
*Parses 10 raw CSVs, performs calendar reindexing and holiday forward-fill imputation, builds `dim_date` and `fact_aum`, and populates `data/db/bluestock_mf.db`.*

### 3. Execute Quantitative Risk & Performance Engine (D4, B3, B4)
```bash
python scripts/compute_metrics.py
```
*Computes CAGR, Volatility, Sharpe, Sortino, Alpha, Beta, 10,000-path Monte Carlo, and Markowitz MPT frontier.*

### 4. Run Investor Recommendation & Segmentation Engine (D6)
```bash
python scripts/recommender.py
```
*Performs K-Means persona clustering, multi-horizon Value at Risk calculation, and multi-factor fund matching.*

### 5. Run Live AMFI NAV Ingestion (B1)
```bash
python scripts/live_nav_fetch.py
```
*Pulls latest NAV quotes from AMFI API and updates `fact_nav` in SQLite database.*

### 6. Open Power BI Executive Dashboard (D5)
```text
Open dashboard/bluestock_mf.pbix in Power BI Desktop to explore interactive visual reports.
```

---

## 8. Automated Ingestion Scheduling (Cron & Windows Task Scheduler)

### Windows Task Scheduler Configuration (Production PowerShell)
To run the automated AMFI live NAV synchronization every weekday at 20:00 IST:

```powershell
$RepoRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$ScriptPath = Join-Path $RepoRoot "scripts\live_nav_fetch.py"

$Action = New-ScheduledTaskAction -Execute $VenvPython `
    -Argument $ScriptPath `
    -WorkingDirectory $RepoRoot

$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday -At 8:00PM

Register-ScheduledTask -TaskName "Bluestock_LiveNAV_Sync" -Action $Action -Trigger $Trigger -Description "Syncs daily closing NAV from AMFI API into SQLite Warehouse"
```

### Linux / macOS Cron Configuration
To configure an equivalent cron daemon job on Unix servers:

```bash
crontab -e
0 20 * * 1-5 /path/to/bluestock_mf_capstone/.venv/bin/python /path/to/bluestock_mf_capstone/scripts/live_nav_fetch.py
```

---

*Bluestock Fintech Mutual Fund Analytics Platform | Lead Data Engineer & Financial Analytics Handover Complete* 🚀
