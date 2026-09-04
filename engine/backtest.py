"""
Simulates each allocation method rebalancing over real historical data,
with a rolling lookback window (no look-ahead bias) and transaction costs
applied on every rebalance. Compares against a naive equal-weight baseline.
"""

import pandas as pd

from engine.returns import align_trading_days, compute_returns
from engine.allocators import (
    annualized_mean_returns,
    markowitz_min_variance,
    risk_parity,
    kelly_portfolio,
    kelly_portfolio_bounded,
    normalize_weights,
)
from engine.config import (
    BACKTEST_LOOKBACK_DAYS,
    BACKTEST_REBALANCE_FREQ,
    BACKTEST_TRANSACTION_COST_BPS,
)


def get_rebalance_dates(dates: pd.DatetimeIndex, freq: str = "M") -> pd.DatetimeIndex:
    """
    Returns the first trading day of each calendar month (freq="M") or
    quarter (freq="Q") present in `dates`. These are the days we'll
    recompute target weights and trade back to them.
    """
    series = pd.Series(dates, index=dates)
    if freq == "M":
        grouped = series.groupby([dates.year, dates.month]).first()
    elif freq == "Q":
        grouped = series.groupby([dates.year, dates.quarter]).first()
    else:
        raise ValueError(f"Unsupported freq: {freq!r}, use 'M' or 'Q'")
    return pd.DatetimeIndex(grouped.values)


def compute_target_weights(method: str, returns_window: pd.DataFrame) -> pd.Series:
    """
    Dispatches to the correct allocation method, using ONLY the returns
    inside returns_window (a trailing slice ending strictly before the
    current rebalance date — no look-ahead into future data).
    """
    mean_returns = annualized_mean_returns(returns_window)
    cov = returns_window.cov() * 252

    if method == "markowitz":
        return markowitz_min_variance(mean_returns, cov)
    elif method == "risk_parity":
        return risk_parity(cov)
    elif method == "kelly":
        return kelly_portfolio_bounded(mean_returns, cov)
    elif method == "equal_weight":
        n = len(mean_returns)
        return pd.Series(1 / n, index=mean_returns.index)
    else:
        raise ValueError(f"Unknown method: {method!r}")


def run_backtest(
    prices: pd.DataFrame,
    method: str,
    lookback_days: int = BACKTEST_LOOKBACK_DAYS,
    rebalance_freq: str = BACKTEST_REBALANCE_FREQ,
    transaction_cost_bps: float = BACKTEST_TRANSACTION_COST_BPS,
    initial_value: float = 1.0,
) -> dict:
    """
    Runs a full walk-forward backtest for one allocation method.

    At each rebalance date, computes target weights using only the
    trailing `lookback_days` of returns (data BEFORE that date, never
    including it — this is what avoids look-ahead bias). Applies a
    transaction cost proportional to turnover, then holds those weights,
    letting them drift day-to-day with price changes, until the next
    rebalance date.

    Returns a dict with 'equity_curve' (portfolio value over time) and
    'turnover_log' (turnover and cost paid at each rebalance).
    """
    prices = align_trading_days(prices)
    returns = compute_returns(prices)
    all_dates = returns.index

    if lookback_days >= len(all_dates):
        raise ValueError("Not enough historical data for the requested lookback window.")

    rebalance_dates = set(get_rebalance_dates(all_dates, freq=rebalance_freq))

    weights = None
    portfolio_value = initial_value
    values = []
    turnover_records = []

    for pos in range(lookback_days, len(all_dates)):
        date = all_dates[pos]

        if date in rebalance_dates or weights is None:
            # Trailing window strictly BEFORE `date` — this is the no-lookahead rule.
            window = returns.iloc[pos - lookback_days: pos]
            target_weights = compute_target_weights(method, window)

            if weights is None:
                turnover = target_weights.abs().sum()  # first buy-in from cash
            else:
                turnover = (target_weights - weights).abs().sum()

            cost = turnover * (transaction_cost_bps / 10000)
            portfolio_value *= (1 - cost)
            weights = target_weights
            turnover_records.append({"date": date, "turnover": turnover, "cost": cost})

        day_return = float((weights * returns.iloc[pos]).sum())
        portfolio_value *= (1 + day_return)
        if portfolio_value <= 0:
            print(f"WARNING: portfolio value hit zero/negative on {date} for this run — "
                  f"likely excessive leverage in the allocator's weights.")
        values.append({"date": date, "value": portfolio_value})

        # Weights drift with each asset's own return until the next rebalance.
        weights = weights * (1 + returns.iloc[pos])
        weights = weights / weights.sum()

    equity_curve = pd.DataFrame(values).set_index("date")["value"]
    turnover_log = pd.DataFrame(turnover_records).set_index("date")

    return {"equity_curve": equity_curve, "turnover_log": turnover_log}