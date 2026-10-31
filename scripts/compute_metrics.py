import numpy as np
import pandas as pd
import scipy.optimize as sco
from pathlib import Path
from typing import Dict, Any, Tuple, List

def calculate_scheme_metrics(nav_series: pd.Series, benchmark_series: pd.Series = None, risk_free_rate: float = 0.06) -> Dict[str, float]:
    clean_nav = nav_series.dropna().sort_index()
    n_days = len(clean_nav)
    if n_days < 2:
        return {}

    daily_returns = clean_nav.pct_change().dropna()
    initial_nav = clean_nav.iloc[0]
    final_nav = clean_nav.iloc[-1]
    
    annualization_factor = 252.0 / n_days
    cagr = (final_nav / initial_nav) ** annualization_factor - 1.0
    volatility = daily_returns.std() * np.sqrt(252.0)
    
    excess_return = cagr - risk_free_rate
    sharpe_ratio = excess_return / volatility if volatility > 0 else 0.0
    
    downside_returns = daily_returns[daily_returns < 0]
    downside_std = np.sqrt(np.mean(downside_returns ** 2)) * np.sqrt(252.0) if len(downside_returns) > 0 else 0.0
    sortino_ratio = excess_return / downside_std if downside_std > 0 else 0.0
    
    cum_max = clean_nav.cummax()
    drawdown = (clean_nav - cum_max) / cum_max
    max_drawdown = float(drawdown.min())

    beta = 1.0
    alpha = 0.0
    if benchmark_series is not None:
        common_idx = clean_nav.index.intersection(benchmark_series.index)
        if len(common_idx) > 10:
            s_ret = clean_nav.loc[common_idx].pct_change().dropna()
            b_ret = benchmark_series.loc[common_idx].pct_change().dropna()
            cov_mat = np.cov(s_ret, b_ret)
            cov_sb = cov_mat[0, 1]
            var_b = cov_mat[1, 1]
            if var_b > 0:
                beta = float(cov_sb / var_b)
                bench_cagr = (benchmark_series.loc[common_idx].iloc[-1] / benchmark_series.loc[common_idx].iloc[0]) ** (252.0 / len(common_idx)) - 1.0
                alpha = float(cagr - (risk_free_rate + beta * (bench_cagr - risk_free_rate)))

    return {
        "n_trading_days": n_days,
        "cagr": float(cagr),
        "annualized_volatility": float(volatility),
        "sharpe_ratio": float(sharpe_ratio),
        "sortino_ratio": float(sortino_ratio),
        "max_drawdown": max_drawdown,
        "beta": beta,
        "alpha": alpha
    }

def run_monte_carlo_simulation(initial_nav: float, mu: float, sigma: float, n_years: int = 5, n_paths: int = 10000, seed: int = 42) -> Dict[str, Any]:
    np.random.seed(seed)
    n_steps = n_years * 252
    dt = 1.0 / 252.0
    
    drift = (mu - 0.5 * (sigma ** 2)) * dt
    diffusion = sigma * np.sqrt(dt)
    
    random_shocks = np.random.normal(0, 1, (n_steps, n_paths))
    daily_factors = np.exp(drift + diffusion * random_shocks)
    
    price_paths = np.empty((n_steps + 1, n_paths))
    price_paths[0] = initial_nav
    price_paths[1:] = initial_nav * np.cumprod(daily_factors, axis=0)
    
    p5 = np.percentile(price_paths, 5, axis=1)
    p50 = np.percentile(price_paths, 50, axis=1)
    p95 = np.percentile(price_paths, 95, axis=1)
    
    return {
        "n_paths": n_paths,
        "n_steps": n_steps,
        "terminal_p5": float(p5[-1]),
        "terminal_p50": float(p50[-1]),
        "terminal_p95": float(p95[-1]),
        "percentile_5_curve": p5,
        "percentile_50_curve": p50,
        "percentile_95_curve": p95
    }

def optimize_markowitz_portfolio(returns_df: pd.DataFrame, risk_free_rate: float = 0.06) -> Dict[str, Any]:
    mean_daily_returns = returns_df.mean()
    cov_matrix = returns_df.cov() * 252.0
    expected_annual_returns = (1.0 + mean_daily_returns) ** 252.0 - 1.0
    n_assets = len(returns_df.columns)
    
    def portfolio_performance(weights):
        p_ret = np.dot(weights, expected_annual_returns)
        p_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        return p_ret, p_vol

    def neg_sharpe(weights):
        p_ret, p_vol = portfolio_performance(weights)
        return -(p_ret - risk_free_rate) / p_vol if p_vol > 0 else 1e6

    def portfolio_vol(weights):
        return portfolio_performance(weights)[1]

    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0})
    bounds = tuple((0.0, 1.0) for _ in range(n_assets))
    init_guess = n_assets * [1.0 / n_assets]

    res_sharpe = sco.minimize(neg_sharpe, init_guess, method='SLSQP', bounds=bounds, constraints=constraints)
    max_sharpe_weights = res_sharpe.x
    ms_ret, ms_vol = portfolio_performance(max_sharpe_weights)
    ms_sharpe = (ms_ret - risk_free_rate) / ms_vol

    res_minvol = sco.minimize(portfolio_vol, init_guess, method='SLSQP', bounds=bounds, constraints=constraints)
    min_vol_weights = res_minvol.x
    mv_ret, mv_vol = portfolio_performance(min_vol_weights)
    mv_sharpe = (mv_ret - risk_free_rate) / mv_vol

    return {
        "assets": list(returns_df.columns),
        "max_sharpe": {
            "weights": {asset: float(w) for asset, w in zip(returns_df.columns, max_sharpe_weights)},
            "expected_return": float(ms_ret),
            "volatility": float(ms_vol),
            "sharpe_ratio": float(ms_sharpe)
        },
        "min_volatility": {
            "weights": {asset: float(w) for asset, w in zip(returns_df.columns, min_vol_weights)},
            "expected_return": float(mv_ret),
            "volatility": float(mv_vol),
            "sharpe_ratio": float(mv_sharpe)
        }
    }

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    nav_file = base_dir / "data" / "processed" / "fact_nav.csv"
    if nav_file.exists():
        df_n = pd.read_csv(nav_file)
        first_amfi = df_n['amfi_code'].iloc[0]
        s_nav = df_n[df_n['amfi_code'] == first_amfi].set_index('nav_date')['nav']
        metrics = calculate_scheme_metrics(s_nav)
        print("Calculated Metrics for Scheme", first_amfi, ":", metrics)
        
        mc = run_monte_carlo_simulation(initial_nav=float(s_nav.iloc[-1]), mu=metrics['cagr'], sigma=metrics['annualized_volatility'])
        print("Monte Carlo 10,000 Paths Terminal P50:", mc['terminal_p50'])

