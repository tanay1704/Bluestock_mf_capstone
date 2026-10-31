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

SELECT 
    strftime('%Y-%m', transaction_date) AS txn_month,
    SUM(CASE WHEN transaction_type = 'SIP' THEN amount_inr ELSE 0 END) AS sip_volume,
    SUM(CASE WHEN transaction_type = 'Lumpsum' THEN amount_inr ELSE 0 END) AS lumpsum_volume,
    SUM(CASE WHEN transaction_type = 'Redemption' THEN amount_inr ELSE 0 END) AS redemption_volume,
    SUM(CASE WHEN transaction_type IN ('SIP', 'Lumpsum') THEN amount_inr ELSE -amount_inr END) AS net_inflow
FROM fact_transactions
GROUP BY strftime('%Y-%m', transaction_date)
ORDER BY txn_month;

SELECT 
    c.cluster,
    c.cluster_label,
    COUNT(DISTINCT c.investor_id) AS investor_count,
    ROUND(AVG(c.annual_income), 2) AS avg_annual_income_lakh,
    ROUND(AVG(c.total_invested), 2) AS avg_total_invested_inr,
    ROUND(AVG(c.txn_count), 2) AS avg_txn_count
FROM clustered_investors c
GROUP BY c.cluster, c.cluster_label
ORDER BY c.cluster;

SELECT 
    fund_house,
    COUNT(*) AS total_schemes,
    SUM(aum_crore) AS total_aum_crore,
    ROUND(AVG(return_3yr_pct), 2) AS avg_3yr_return_pct,
    ROUND(AVG(sharpe_ratio), 2) AS avg_sharpe_ratio
FROM fact_performance
GROUP BY fund_house
ORDER BY total_aum_crore DESC;

SELECT 
    city_tier,
    COUNT(*) AS transaction_count,
    SUM(amount_inr) AS total_amount_inr,
    ROUND(AVG(amount_inr), 2) AS avg_ticket_inr,
    ROUND(SUM(amount_inr) * 100.0 / (SELECT SUM(amount_inr) FROM fact_transactions), 2) AS volume_share_pct
FROM fact_transactions
GROUP BY city_tier
ORDER BY total_amount_inr DESC;

SELECT 
    category,
    COUNT(*) AS scheme_count,
    ROUND(AVG(return_1yr_pct), 2) AS avg_1yr_ret_pct,
    ROUND(AVG(return_3yr_pct), 2) AS avg_3yr_ret_pct,
    ROUND(AVG(std_dev_ann_pct), 2) AS avg_volatility_pct,
    ROUND(AVG(expense_ratio_pct), 2) AS avg_expense_ratio_pct
FROM fact_performance
GROUP BY category
ORDER BY avg_3yr_ret_pct DESC;

SELECT 
    p.amfi_code,
    f.scheme_name,
    COUNT(*) AS total_transactions,
    SUM(t.amount_inr) AS total_gross_flow_inr,
    p.return_3yr_pct,
    p.sharpe_ratio
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
JOIN fact_transactions t ON p.amfi_code = t.amfi_code
GROUP BY p.amfi_code, f.scheme_name, p.return_3yr_pct, p.sharpe_ratio
ORDER BY total_gross_flow_inr DESC
LIMIT 10;

SELECT 
    f.category,
    ROUND(AVG(p.alpha), 2) AS avg_alpha,
    ROUND(AVG(p.beta), 2) AS avg_beta,
    ROUND(AVG(p.sharpe_ratio), 2) AS avg_sharpe,
    ROUND(AVG(p.sortino_ratio), 2) AS avg_sortino,
    ROUND(AVG(p.max_drawdown_pct), 2) AS avg_max_drawdown_pct
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
GROUP BY f.category
ORDER BY avg_sharpe DESC;

SELECT 
    kyc_status,
    payment_mode,
    COUNT(*) AS transaction_count,
    SUM(amount_inr) AS total_volume_inr
FROM fact_transactions
GROUP BY kyc_status, payment_mode
ORDER BY total_volume_inr DESC;
