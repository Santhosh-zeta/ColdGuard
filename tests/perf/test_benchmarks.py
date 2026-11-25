"""Reproducible Monte Carlo workloads (run with --benchmark-only)."""

import numpy as np
import pytest

from core.bayesian import monte_carlo_potency_distribution
from core.vaccine_params import VACCINE_DB

SEED = 42


@pytest.mark.parametrize(
    ("n_samples", "n_readings"),
    [
        pytest.param(5_000, 1_000, id="large-log"),
        pytest.param(20_000, 100, id="many-samples"),
        pytest.param(1_000, 24, id="mobile-sized"),
    ],
)
def test_monte_carlo(benchmark, n_samples: int, n_readings: int) -> None:
    timestamps = np.arange(n_readings, dtype=np.float64) * 3600
    temperatures = 5.0 + np.sin(np.arange(n_readings) * 2 * np.pi / 24)
    params = VACCINE_DB["DPT"]

    def setup():
        # Reset the RNG outside each measured round for comparable workloads.
        return (
            (timestamps, temperatures, params),
            {"n_samples": n_samples, "rng": np.random.default_rng(SEED)},
        )

    result = benchmark.pedantic(
        monte_carlo_potency_distribution,
        setup=setup,
        rounds=7,
        iterations=1,
        warmup_rounds=1,
    )

    assert result.shape == (n_samples,)
    assert np.isfinite(result).all()
    assert np.all((result >= 0) & (result <= 1))
