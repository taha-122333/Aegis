"""
Unit tests for the allocators module. Uses a small synthetic 3-asset
return dataset with known, hand-checkable statistical properties.
"""

import numpy as np
import pandas as pd
import pytest

from engine.allocators import (
    annualized_mean_returns,
    markowitz_min_variance,
    risk_parity,
    kelly_portfolio,
    normalize_weights,
    portfolio_performance,
)


@pytest.fixture
def sample_returns():
    np.random.seed(42)
    n_days = 500
    data = {
        "LOW_VOL": np.random.normal(0.0003, 0.005, n_days),
        "MED_VOL": np.random.normal(0.0005, 0.012, n_days),
        "HIGH_VOL": np.random.normal(0.0008, 0.025, n_days),
    }
    return pd.DataFrame(data)


def test_markowitz_weights_sum_to_one(sample_returns):
    mean_returns = annualized_mean_returns(sample_returns)
    cov = sample_returns.cov() * 252
    weights = markowitz_min_variance(mean_returns, cov)
    assert np.isclose(weights.sum(), 1.0, atol=1e-4)
    assert (weights >= -1e-6).all()  # no meaningful negative (short) weights


def test_markowitz_min_variance_is_low_risk(sample_returns):
    mean_returns = annualized_mean_returns(sample_returns)
    cov = sample_returns.cov() * 252
    weights = markowitz_min_variance(mean_returns, cov)
    _, vol = portfolio_performance(weights.values, mean_returns, cov)
    # An all-in-the-riskiest-asset portfolio should be more volatile
    naive_weights = np.array([0, 0, 1.0])
    _, naive_vol = portfolio_performance(naive_weights, mean_returns, cov)
    assert vol < naive_vol


def test_risk_parity_weights_sum_to_one(sample_returns):
    cov = sample_returns.cov() * 252
    weights = risk_parity(cov)
    assert np.isclose(weights.sum(), 1.0, atol=1e-4)
    assert (weights > 0).all()


def test_risk_parity_favors_low_vol_asset(sample_returns):
    cov = sample_returns.cov() * 252
    weights = risk_parity(cov)
    # The lowest-volatility asset should get the largest weight, since it
    # takes more of it to contribute an equal share of risk.
    assert weights["LOW_VOL"] > weights["HIGH_VOL"]


def test_kelly_normalized_sums_to_one(sample_returns):
    mean_returns = annualized_mean_returns(sample_returns)
    cov = sample_returns.cov() * 252
    raw = kelly_portfolio(mean_returns, cov)
    normalized = normalize_weights(raw)
    assert np.isclose(normalized.sum(), 1.0, atol=1e-4)