"""
Bayesian / Monte Carlo layer for uncertainty quantification.

Samples over kinetic parameter uncertainty and logger measurement noise to
produce a posterior distribution of vaccine potency.
"""

from __future__ import annotations

import math
from typing import Optional

import numpy as np

from .arrhenius import integrate_degradation, compute_freeze_damage_fraction
from .vaccine_params import VaccineParams


def monte_carlo_potency_distribution(
    timestamps: np.ndarray,
    temperatures_C: np.ndarray,
    vaccine_params: VaccineParams,
    n_samples: int = 5_000,
    initial_potency: float = 1.0,
    logger_accuracy_C: float = 0.5,
    rng: Optional[np.random.Generator] = None,
) -> np.ndarray:
    """Return a Monte-Carlo sample of final potency values.

    For each sample:
      1. Draw Ea ~ Normal(Ea_mean, Ea_std)
      2. Draw log(A) ~ Normal(log(A), A_log_std), i.e. A is log-normal
      3. Add independent Gaussian noise ~ N(0, logger_accuracy_C) to every
         temperature reading
      4. Compute potency via integrate_degradation

    Parameters
    ----------
    timestamps : array-like
        Unix timestamps (seconds).
    temperatures_C : array-like
        Recorded temperatures in °C, one per timestamp.
    vaccine_params : VaccineParams
        Kinetic parameters with their uncertainty.
    n_samples : int
        Number of Monte-Carlo draws.
    initial_potency : float
        Potency at t=0 (fraction in [0,1]).
    logger_accuracy_C : float
        1-sigma accuracy of the data-logger in °C.
    rng : np.random.Generator, optional
        Random number generator for reproducibility.

    Returns
    -------
    np.ndarray
        Array of shape (n_samples,) with potency fractions in [0, 1].
    """
    if rng is None:
        rng = np.random.default_rng()

    ts = np.asarray(timestamps, dtype=float)
    tc = np.asarray(temperatures_C, dtype=float)

    # --- sample Ea (Normal)
    Ea_samples = rng.normal(
        vaccine_params.Ea_mean, vaccine_params.Ea_std, size=n_samples
    )

    # --- sample A (log-normal)
    log_A_mean = math.log(vaccine_params.A)
    log_A_samples = rng.normal(log_A_mean, vaccine_params.A_log_std, size=n_samples)
    A_samples = np.exp(log_A_samples)

    # --- temperature noise: shape (n_samples, len(tc))
    noise = rng.normal(0.0, logger_accuracy_C, size=(n_samples, len(tc)))
    tc_perturbed = tc[np.newaxis, :] + noise  # broadcast

    # Freeze damage is determined from actual measured temperatures (not perturbed),
    # because freeze damage is a binary event based on observed data, not a kinetic
    # uncertainty. The same retention factor applies to all MC samples.
    freeze_retention = compute_freeze_damage_fraction(ts, tc, vaccine_params)

    potencies = np.empty(n_samples, dtype=float)
    for i in range(n_samples):
        D = integrate_degradation(ts, tc_perturbed[i], Ea_samples[i], A_samples[i])
        potencies[i] = initial_potency * math.exp(-D) * freeze_retention

    # Clamp to [0, 1]
    potencies = np.clip(potencies, 0.0, 1.0)
    return potencies


def compute_posterior_summary(potency_samples: np.ndarray) -> dict:
    """Compute summary statistics from the posterior potency distribution.

    Parameters
    ----------
    potency_samples : np.ndarray
        Array of potency fractions from monte_carlo_potency_distribution.

    Returns
    -------
    dict with keys:
        mean, median, std,
        ci_90_lower, ci_90_upper,
        ci_95_lower, ci_95_upper,
        prob_above_80pct, prob_above_67pct
    """
    s = np.asarray(potency_samples, dtype=float)
    return {
        "mean": float(np.mean(s)),
        "median": float(np.median(s)),
        "std": float(np.std(s, ddof=1)),
        "ci_90_lower": float(np.percentile(s, 5.0)),
        "ci_90_upper": float(np.percentile(s, 95.0)),
        "ci_95_lower": float(np.percentile(s, 2.5)),
        "ci_95_upper": float(np.percentile(s, 97.5)),
        "prob_above_80pct": float(np.mean(s >= 0.80)),
        "prob_above_67pct": float(np.mean(s >= 0.67)),
    }
