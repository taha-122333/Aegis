"""
Unit tests for the returns module. Uses a small hand-built price series so
we know exactly what the correct answer should be, instead of relying on
real downloaded data (which changes every day).
"""

import numpy as np
import pandas as pd

from engine.returns import (
    compute_returns,
    compute_log_returns,
    compute_covariance,
    compute_correlation,
)


def _sample_prices():
    return pd.DataFrame(
        {
            "A": [100, 110, 121, 108.9],
            "B": [50, 52.5, 50, 55],
        }
    )


def test_compute_returns_basic():
    prices = _sample_prices()
    returns = compute_returns(prices)
    assert np.isclose(returns["A"].iloc[0], 0.10)
    assert not returns.isna().any().any()


def test_compute_log_returns_basic():
    prices = _sample_prices()
    log_returns = compute_log_returns(prices)
    expected_first = np.log(110 / 100)
    assert np.isclose(log_returns["A"].iloc[0], expected_first)


def test_covariance_matrix_shape_and_symmetry():
    prices = _sample_prices()
    returns = compute_returns(prices)
    cov = compute_covariance(returns, annualize=False)
    assert cov.shape == (2, 2)
    assert np.isclose(cov.loc["A", "B"], cov.loc["B", "A"])


def test_correlation_matrix_diagonal_is_one():
    prices = _sample_prices()
    returns = compute_returns(prices)
    corr = compute_correlation(returns)
    assert np.isclose(corr.loc["A", "A"], 1.0)
    assert np.isclose(corr.loc["B", "B"], 1.0)
    assert (corr.values <= 1.0001).all() and (corr.values >= -1.0001).all()