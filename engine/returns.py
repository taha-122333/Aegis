"""
Turns raw prices into returns, and returns into the covariance/correlation
matrices that the allocators in later sprints will need.
"""

import numpy as np
import pandas as pd


def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Simple daily percentage returns: (price_today - price_yesterday) / price_yesterday.
    """
    returns = prices.pct_change()
    return returns.dropna(how="all")


def compute_log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Log returns: ln(price_today / price_yesterday). Log returns are additive
    over time, which is why quant finance tends to prefer them for statistics
    like covariance.
    """
    log_returns = np.log(prices / prices.shift(1))
    return log_returns.dropna(how="all")


def compute_covariance(returns: pd.DataFrame, annualize: bool = True) -> pd.DataFrame:
    """
    Covariance matrix of returns: measures how much each pair of assets
    moves together. annualize=True scales daily covariance up to a yearly
    figure (x252, the typical number of trading days in a year).
    """
    cov = returns.cov()
    if annualize:
        cov = cov * 252
    return cov


def compute_correlation(returns: pd.DataFrame) -> pd.DataFrame:
    """
    Correlation matrix: covariance normalized to always sit between -1 and 1.
    1 = always move together, -1 = always move opposite, 0 = no relationship.
    """
    return returns.corr()