"""
Unit tests for monte_carlo.py. Checks the simulation produces the right
shape, is reproducible with a fixed seed, and that CVaR is consistently
at least as bad as VaR.
"""

import numpy as np

from engine.monte_carlo import simulate_portfolio_paths, monte_carlo_var, monte_carlo_cvar


def test_simulation_shape():
    paths = simulate_portfolio_paths(port_mean=0.10, port_vol=0.15, n_days=100, n_simulations=500)
    assert paths.shape == (500, 101)


def test_simulation_starts_at_initial_value():
    paths = simulate_portfolio_paths(port_mean=0.10, port_vol=0.15, n_days=50, n_simulations=200, initial_value=1.0)
    assert np.allclose(paths[:, 0], 1.0)


def test_simulation_reproducible_with_same_seed():
    paths_a = simulate_portfolio_paths(port_mean=0.10, port_vol=0.15, n_simulations=100, seed=7)
    paths_b = simulate_portfolio_paths(port_mean=0.10, port_vol=0.15, n_simulations=100, seed=7)
    assert np.allclose(paths_a, paths_b)


def test_mc_cvar_at_least_as_bad_as_var():
    paths = simulate_portfolio_paths(port_mean=0.10, port_vol=0.20, n_simulations=5000, seed=1)
    var = monte_carlo_var(paths)
    cvar = monte_carlo_cvar(paths)
    assert cvar >= var