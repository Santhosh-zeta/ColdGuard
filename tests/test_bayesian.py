"""Tests for core.bayesian — Monte Carlo uncertainty propagation."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pytest

from core.bayesian import monte_carlo_potency_distribution, compute_posterior_summary
from core.vaccine_params import VACCINE_DB, VaccineParams


@pytest.fixture
def dpt():
    return VACCINE_DB["DPT"]


def _constant_log(temp_C, duration_hours, n=20):
    ts = np.linspace(0, duration_hours * 3600, n)
    temps = np.full(n, temp_C)
    return ts, temps


def test_returns_correct_number_of_samples(dpt):
    ts, temps = _constant_log(4.0, 24.0)
    samples = monte_carlo_potency_distribution(ts, temps, dpt, n_samples=200)
    assert len(samples) == 200


def test_all_samples_in_unit_interval(dpt):
    ts, temps = _constant_log(10.0, 48.0)
    samples = monte_carlo_potency_distribution(ts, temps, dpt, n_samples=500)
    assert np.all(samples >= 0.0)
    assert np.all(samples <= 1.0)


def test_fixed_seed_reproducible(dpt):
    ts, temps = _constant_log(5.0, 100.0)
    rng1 = np.random.default_rng(42)
    s1 = monte_carlo_potency_distribution(ts, temps, dpt, n_samples=100, rng=rng1)
    rng2 = np.random.default_rng(42)
    s2 = monte_carlo_potency_distribution(ts, temps, dpt, n_samples=100, rng=rng2)
    np.testing.assert_array_equal(s1, s2)


def test_zero_uncertainty_gives_narrow_variance():
    """With Ea_std=0, A_log_std=0, zero logger error → near-zero variance."""
    narrow = VaccineParams(
        name="Test", Ea_mean=83_000, Ea_std=0.0, A=3.37e10, A_log_std=0.0,
        shelf_life_hours=17_280, ref_temp_K=278.15,
        min_potency_threshold=0.80, freeze_sensitive=False
    )
    ts = np.linspace(0, 48 * 3600, 50)
    temps = np.full(50, 5.0)
    samples = monte_carlo_potency_distribution(
        ts, temps, narrow, n_samples=500, logger_accuracy_C=0.0
    )
    assert np.std(samples) < 1e-6


def test_wider_ea_std_gives_wider_ci(dpt):
    ts, temps = _constant_log(15.0, 72.0)
    np.random.seed(0)
    s_narrow = monte_carlo_potency_distribution(ts, temps, dpt, n_samples=1000)
    wide = VaccineParams(
        name=dpt.name, Ea_mean=dpt.Ea_mean, Ea_std=dpt.Ea_std * 5,
        A=dpt.A, A_log_std=dpt.A_log_std * 5,
        shelf_life_hours=dpt.shelf_life_hours, ref_temp_K=dpt.ref_temp_K,
        min_potency_threshold=dpt.min_potency_threshold,
        freeze_sensitive=dpt.freeze_sensitive
    )
    np.random.seed(0)
    s_wide = monte_carlo_potency_distribution(ts, temps, wide, n_samples=1000)
    assert np.std(s_wide) > np.std(s_narrow)


def test_posterior_summary_keys(dpt):
    ts, temps = _constant_log(5.0, 24.0)
    samples = monte_carlo_potency_distribution(ts, temps, dpt, n_samples=200)
    summary = compute_posterior_summary(samples)
    required = {"mean", "median", "ci_90_lower", "ci_90_upper",
                "ci_95_lower", "ci_95_upper", "prob_above_80pct",
                "prob_above_67pct", "std"}
    assert required.issubset(summary.keys())


def test_posterior_summary_ordering(dpt):
    ts, temps = _constant_log(5.0, 24.0)
    samples = monte_carlo_potency_distribution(ts, temps, dpt, n_samples=500)
    s = compute_posterior_summary(samples)
    assert s["ci_95_lower"] <= s["ci_90_lower"] <= s["mean"] <= s["ci_90_upper"] <= s["ci_95_upper"]
