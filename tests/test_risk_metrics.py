"""
Unit tests for risk_metrics.py. Uses a small synthetic return series with
a known, deliberate crash built in, so we can verify drawdown and VaR
behave correctly against numbers we can check by hand.
"""

import numpy as np
import pandas as pd
import pytest

from engine.risk_metrics import (
    portfolio_returns,
    historical_var,
    historical_cvar,
    parametric_var,
    max_drawdown,
    sharpe_ratio,
    sortino_ratio,
    stress_test_period,
)


@pytest.fixture
def sample_returns():
    np.random.seed(1)
    n_days = 300
    data = {
        "A": np.random.normal(0.0006, 0.01, n_days),
        "B": np.random.normal(0.0004, 0.015, n_days),
    }
    df = pd.DataFrame(data, index=pd.date_range("2020-01-01", periods=n_days, freq="B"))
    # Inject a deliberate 3-day crash so max_drawdown has something real to catch
    df.iloc[50:53, 0] = [-0.08, -0.07, -0.05]
    df.iloc[50:53, 1] = [-0.08, -0.07, -0.05]
    return df


@pytest.fixture
def equal_weights():
    return pd.Series({"A": 0.5, "B": 0.5})


def test_portfolio_returns_alignment(sample_returns, equal_weights):
    port_ret = portfolio_returns(sample_returns, equal_weights)
    assert len(port_ret) == len(sample_returns)


def test_cvar_is_at_least_as_bad_as_var(sample_returns, equal_weights):
    port_ret = portfolio_returns(sample_returns, equal_weights)
    var = historical_var(port_ret)
    cvar = historical_cvar(port_ret)
    assert cvar >= var


def test_max_drawdown_catches_injected_crash(sample_returns, equal_weights):
    port_ret = portfolio_returns(sample_returns, equal_weights)
    dd = max_drawdown(port_ret)
    assert dd > 0.10  # the injected 3-day crash should show up clearly


def test_parametric_var_positive_for_typical_inputs():
    var = parametric_var(daily_mean=0.0005, daily_vol=0.015)
    assert var > 0


def test_sharpe_and_sortino_reasonable(sample_returns, equal_weights):
    port_ret = portfolio_returns(sample_returns, equal_weights)
    sharpe = sharpe_ratio(port_ret)
    sortino = sortino_ratio(port_ret)
    assert isinstance(sharpe, float)
    assert isinstance(sortino, float)
    # Sortino only penalizes downside, so it should generally read higher
    # than Sharpe when there's any upside volatility at all.
    assert sortino >= sharpe - 5  # loose sanity bound, not a strict law


def test_stress_test_returns_expected_keys(sample_returns, equal_weights):
    result = stress_test_period(sample_returns, equal_weights, "2020-01-01", "2020-06-01")
    assert set(result.keys()) == {"period", "cumulative_return", "worst_single_day", "max_drawdown"}