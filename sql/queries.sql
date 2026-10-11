-- ==============================================================================
-- BLUESTOCK MUTUAL FUND ANALYTICS PLATFORM
-- Key Business Intelligence & Verification Queries
-- ==============================================================================

-- 1. Reconcile Gross Transaction Volume by Type (Reconciles to INR 3,521,580,430)
SELECT 
    transaction_type,
    COUNT(*) AS total_transactions,
    SUM(amount_inr) AS total_volume_inr,
    ROUND(SUM(amount_inr) / 10000000.0, 2) AS volume_in_crores,
    ROUND(SUM(amount_inr) / 1000000000.0, 3) AS volume_in_billions,
    ROUND(AVG(amount_inr), 2) AS avg_ticket_size_inr
FROM fact_transactions
GROUP BY transaction_type
ORDER BY total_volume_inr DESC;

-- 2. Top Performing Mutual Funds by 3-Year Return
SELECT 
    f.scheme_name,
    f.fund_house,
    f.category,
    p.return_3yr_pct,
    p.sharpe_ratio,
    p.aum_crore
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
ORDER BY p.return_3yr_pct DESC
LIMIT 10;

-- 3. Monthly Transaction Inflows vs Outflows
SELECT 
    strftime('%Y-%m', transaction_date) AS txn_month,
    SUM(CASE WHEN transaction_type = 'SIP' THEN amount_inr ELSE 0 END) AS sip_volume,
    SUM(CASE WHEN transaction_type = 'Lumpsum' THEN amount_inr ELSE 0 END) AS lumpsum_volume,
    SUM(CASE WHEN transaction_type = 'Redemption' THEN amount_inr ELSE 0 END) AS redemption_volume,
    SUM(CASE WHEN transaction_type IN ('SIP', 'Lumpsum') THEN amount_inr ELSE -amount_inr END) AS net_inflow
FROM fact_transactions
GROUP BY strftime('%Y-%m', transaction_date)
ORDER BY txn_month;

-- 4. Investor Segmentation Breakdown (Joins fact_transactions with clustered_investors)
SELECT 
    c.cluster,
    COUNT(DISTINCT c.investor_id) AS investor_count,
    ROUND(AVG(c.annual_income), 2) AS avg_annual_income_lakh,
    ROUND(AVG(c.total_invested), 2) AS avg_total_invested_inr,
    ROUND(AVG(c.txn_count), 2) AS avg_txn_count
FROM clustered_investors c
GROUP BY c.cluster
ORDER BY c.cluster;
