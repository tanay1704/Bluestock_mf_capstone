# Bluestock Mutual Fund Analytics Platform - Data Dictionary

This data dictionary outlines the metadata, data types, physical constraints, business definitions, and unit scales across all star-schema entities and operational datasets in the Bluestock Fintech platform.

---

## 1. Dimension Tables

### 1.1 `dim_fund`
*Grain: One record per registered mutual fund scheme (`amfi_code`).*

| Column Name | Data Type | Nullable | Primary / Foreign Key | Description & Permissible Values |
| :--- | :--- | :--- | :--- | :--- |
| `amfi_code` | `BIGINT` | No | **Primary Key** | Unique 6-digit Association of Mutual Funds in India (AMFI) scheme identifier. |
| `fund_house` | `TEXT` | No | — | Asset Management Company (AMC) name (e.g., 'SBI Mutual Fund', 'HDFC Mutual Fund'). |
| `scheme_name` | `TEXT` | No | — | Full regulatory mutual fund scheme name. |
| `category` | `TEXT` | No | — | High-level asset class category ('Equity', 'Debt', 'Hybrid', 'Solution Oriented'). |
| `sub_category` | `TEXT` | Yes | — | SEBI-defined sub-classification ('Small Cap', 'Mid Cap', 'Large Cap', 'Flexi Cap'). |
| `plan` | `TEXT` | Yes | — | Investment distribution plan ('Regular', 'Direct'). |
| `launch_date` | `TEXT` | Yes | — | Inception date of the mutual fund scheme (YYYY-MM-DD). |
| `benchmark` | `TEXT` | Yes | — | Primary market benchmark index against which alpha/beta are measured. |
| `expense_ratio_pct`| `FLOAT` | Yes | — | Total Expense Ratio (TER) expressed as a percentage (Bounded strictly: 0.10% – 2.50%). |
| `exit_load_pct` | `FLOAT` | Yes | — | Redemption exit fee percentage if liquidated before mandatory holding threshold. |
| `min_sip_amount` | `BIGINT` | Yes | — | Minimum recurring monthly contribution requirement in whole Indian Rupees (INR). |
| `min_lumpsum_amount`| `BIGINT` | Yes | — | Minimum one-time capital commitment in whole Indian Rupees (INR). |
| `fund_manager` | `TEXT` | Yes | — | Lead portfolio manager name or management team designation. |
| `risk_category` | `TEXT` | Yes | — | SEBI Riskometer grade ('Very High', 'High', 'Moderate', 'Moderately High', 'Low'). |
| `sebi_category_code`| `TEXT` | Yes | — | Regulatory SEBI nomenclature categorization code. |

---

### 1.2 `dim_date`
*Grain: One record per contiguous calendar day.*

| Column Name | Data Type | Nullable | Primary / Foreign Key | Description & Permissible Values |
| :--- | :--- | :--- | :--- | :--- |
| `date_key` | `TEXT` | No | **Primary Key** | ISO 8601 formatted date string key (`YYYY-MM-DD`). |
| `full_date` | `DATE` | No | — | Exact date representation. |
| `year` | `INTEGER` | No | — | Gregorian calendar year (e.g., 2021, 2022, 2023, 2024, 2025). |
| `quarter` | `INTEGER` | No | — | Calendar quarter (1, 2, 3, 4). |
| `month` | `INTEGER` | No | — | Calendar month numerical index (1 through 12). |
| `month_name` | `TEXT` | No | — | Full month designation ('January', 'February', ..., 'December'). |
| `day` | `INTEGER` | No | — | Day of month (1 through 31). |
| `day_of_week` | `INTEGER` | No | — | Zero-indexed day of the week (0 = Monday, 6 = Sunday). |
| `day_name` | `TEXT` | No | — | Full weekday name ('Monday', 'Tuesday', ..., 'Sunday'). |
| `is_weekend` | `INTEGER` | No | — | Binary flag indicating weekend non-trading days (`1` if Saturday/Sunday, else `0`). |

---

### 1.3 `clustered_investors`
*Grain: One record per distinct investor (`investor_id`).*

| Column Name | Data Type | Nullable | Primary / Foreign Key | Description & Permissible Values |
| :--- | :--- | :--- | :--- | :--- |
| `investor_id` | `TEXT` | No | **Primary Key** | Unique synthetic retail investor alphanumeric identifier (`INV000001` - `INV005000`). |
| `total_invested` | `FLOAT` | No | — | Lifetime gross capital committed in whole Indian Rupees (INR). |
| `txn_count` | `INTEGER` | No | — | Total historical orders executed (SIP + Lumpsum + Redemption). |
| `annual_income` | `FLOAT` | No | — | Investor annual gross income in Indian Lakhs (1 Lakh = ₹100,000 INR). |
| `cluster` | `INTEGER` | No | — | Algorithmic K-Means segment assignment (`0`, `1`, `2`). |
| `cluster_label` | `TEXT` | Yes | — | Human-readable cohort persona ('Moderate Retail', 'Affluent HNI', 'Emerging Youth'). |

---

## 2. Fact Tables

### 2.1 `fact_transactions`
*Grain: One record per executed monetary transaction.*

| Column Name | Data Type | Nullable | Primary / Foreign Key | Description & Permissible Values |
| :--- | :--- | :--- | :--- | :--- |
| `transaction_id` | `INTEGER` | No | **Primary Key** | Autoincrementing physical transaction surrogate sequence. |
| `investor_id` | `TEXT` | No | — | Unique investor reference mapped to `clustered_investors(investor_id)`. |
| `transaction_date` | `DATETIME` | No | — | Execution timestamp of transaction settlement. |
| `date_key` | `TEXT` | No | **Foreign Key** | References `dim_date(date_key)`. |
| `amfi_code` | `BIGINT` | No | **Foreign Key** | References `dim_fund(amfi_code)`. |
| `transaction_type` | `TEXT` | No | — | Order flow classification: Strictly bounded to `{'SIP', 'Lumpsum', 'Redemption'}`. |
| `amount_inr` | `BIGINT` | No | — | Transaction monetary value in whole INR (Strict assertion: `amount_inr > 0`). |
| `state` | `TEXT` | Yes | — | Indian state jurisdiction of registered investor residency. |
| `city` | `TEXT` | Yes | — | City of investor residence. |
| `city_tier` | `TEXT` | Yes | — | Geographical market classification ('Tier 1', 'Tier 2'). |
| `age_group` | `TEXT` | Yes | — | Demographic age bracket ('18-25', '26-35', '36-45', '46-60', '60+'). |
| `gender` | `TEXT` | Yes | — | Investor gender demographic. |
| `annual_income_lakh`| `FLOAT` | Yes | — | Annual declared income in Lakhs (₹100,000 units). |
| `payment_mode` | `TEXT` | Yes | — | Settlement channel ('Net Banking', 'UPI', 'Auto-Debit', 'Cheque'). |
| `kyc_status` | `TEXT` | Yes | — | Regulatory KYC compliance state (`'Verified'`, `'Pending'`). |

---

### 2.2 `fact_nav`
*Grain: One record per mutual fund scheme per calendar date.*

| Column Name | Data Type | Nullable | Primary / Foreign Key | Description & Permissible Values |
| :--- | :--- | :--- | :--- | :--- |
| `amfi_code` | `BIGINT` | No | **Composite PK / FK** | References `dim_fund(amfi_code)`. |
| `nav_date` | `DATE` | No | **Composite PK** | Valuation date (continuous calendar time-series, forward-filled on market holidays). |
| `date_key` | `TEXT` | No | **Foreign Key** | References `dim_date(date_key)`. |
| `nav` | `FLOAT` | No | — | Net Asset Value in INR per unit (Strict assertion: `nav > 0`). |
| `daily_return_pct` | `FLOAT` | Yes | — | Percentage price change relative to previous calendar day closing NAV. |

---

### 2.3 `fact_performance`
*Grain: One record per mutual fund scheme summary risk-return metrics.*

| Column Name | Data Type | Nullable | Primary / Foreign Key | Description & Permissible Values |
| :--- | :--- | :--- | :--- | :--- |
| `amfi_code` | `BIGINT` | No | **Primary Key / FK** | References `dim_fund(amfi_code)`. |
| `scheme_name` | `TEXT` | No | — | Fund regulatory name. |
| `fund_house` | `TEXT` | No | — | AMC institutional brand. |
| `category` | `TEXT` | No | — | Scheme category. |
| `plan` | `TEXT` | Yes | — | Plan distribution type. |
| `return_1yr_pct` | `FLOAT` | Yes | — | 1-Year trailing annualized return percentage. |
| `return_3yr_pct` | `FLOAT` | Yes | — | 3-Year Compounded Annual Growth Rate (CAGR) percentage. |
| `return_5yr_pct` | `FLOAT` | Yes | — | 5-Year Compounded Annual Growth Rate (CAGR) percentage. |
| `benchmark_3yr_pct`| `FLOAT` | Yes | — | Benchmark index 3-Year CAGR percentage. |
| `alpha` | `FLOAT` | Yes | — | Jensen's Alpha: Excess return over CAPM expected benchmark return. |
| `beta` | `FLOAT` | Yes | — | Systematic market risk sensitivity relative to underlying benchmark index. |
| `sharpe_ratio` | `FLOAT` | Yes | — | Risk-adjusted performance ratio: $(R_p - R_f) / \sigma_p$ ($R_f = 6.0\%$). |
| `sortino_ratio` | `FLOAT` | Yes | — | Downside risk-adjusted performance ratio: $(R_p - R_f) / \sigma_{down}$. |
| `std_dev_ann_pct` | `FLOAT` | Yes | — | Annualized volatility of daily returns ($\sigma_{daily} \times \sqrt{252}$). |
| `max_drawdown_pct` | `FLOAT` | Yes | — | Peak-to-trough maximum observed historical capital decline percentage. |
| `aum_crore` | `BIGINT` | No | — | Scheme-level Assets Under Management in Crores (1 Crore = ₹10,000,000 INR). |
| `expense_ratio_pct`| `FLOAT` | Yes | — | Scheme Total Expense Ratio percentage. |
| `morningstar_rating`| `BIGINT` | Yes | — | Morningstar rating scale (1 to 5 stars). |
| `risk_grade` | `TEXT` | Yes | — | Institutional qualitative risk assessment score. |

---

### 2.4 `fact_aum`
*Grain: One record per Asset Management Company per reporting period.*

| Column Name | Data Type | Nullable | Primary / Foreign Key | Description & Permissible Values |
| :--- | :--- | :--- | :--- | :--- |
| `aum_id` | `INTEGER` | No | **Primary Key** | Autoincrementing surrogate sequence key. |
| `report_date` | `DATE` | No | — | Reporting month date representation. |
| `date_key` | `TEXT` | No | **Foreign Key** | References `dim_date(date_key)`. |
| `fund_house` | `TEXT` | No | — | Asset Management Company name. |
| `aum_lakh_crore` | `FLOAT` | No | — | Industry-level AUM in Lakh Crores ($10^{12}$ INR). |
| `aum_crore` | `BIGINT` | No | — | Converted AUM in Crores ($10^7$ INR) for unit alignment. |
| `num_schemes` | `INTEGER` | No | — | Total mutual fund offerings managed by the AMC. |

