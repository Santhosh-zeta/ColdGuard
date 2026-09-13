"""
Validate ColdGuard Arrhenius model against published stability data.

Each validation data point represents an isothermal exposure experiment:
  temperature_C, duration_hours → measured_potency.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, Any, Union

import numpy as np
import pandas as pd

from core.arrhenius import arrhenius_k
from core.bayesian import monte_carlo_potency_distribution, compute_posterior_summary
from core.vaccine_params import VACCINE_DB, VaccineParams


def validate_single_point(
    temperature_C: float,
    duration_hours: float,
    measured_potency: float,
    vaccine_params: VaccineParams,
    n_mc_samples: int = 5_000,
    rng=None,
) -> Dict[str, Any]:
    """Validate the model against a single isothermal stability data point.

    Constructs a two-reading temperature log (start, end) at constant temperature
    and runs the Monte-Carlo analysis.

    Parameters
    ----------
    temperature_C : float
    duration_hours : float
    measured_potency : float
        Observed potency as a fraction in [0, 1].
    vaccine_params : VaccineParams
    n_mc_samples : int
    rng : np.random.Generator, optional

    Returns
    -------
    dict with keys:
        temperature_C, duration_hours, measured_potency,
        point_estimate, mc_mean, mc_std,
        ci_95_lower, ci_95_upper,
        bias, within_95ci, residual_pct
    """
    if rng is None:
        rng = np.random.default_rng()

    # Construct isothermal log: two readings, dt = duration_hours
    timestamps = np.array([0.0, duration_hours * 3600.0])
    temperatures = np.array([temperature_C, temperature_C])

    # Point estimate
    k = arrhenius_k(temperature_C + 273.15, vaccine_params.Ea_mean, vaccine_params.A)
    D = k * duration_hours
    point_estimate = math.exp(-D)

    # Monte-Carlo
    samples = monte_carlo_potency_distribution(
        timestamps,
        temperatures,
        vaccine_params,
        n_samples=n_mc_samples,
        rng=rng,
    )
    posterior = compute_posterior_summary(samples)

    bias = posterior["mean"] - measured_potency
    within_ci = (
        posterior["ci_95_lower"] <= measured_potency <= posterior["ci_95_upper"]
    )

    return {
        "temperature_C": temperature_C,
        "duration_hours": duration_hours,
        "measured_potency": measured_potency,
        "point_estimate": point_estimate,
        "mc_mean": posterior["mean"],
        "mc_std": posterior["std"],
        "ci_95_lower": posterior["ci_95_lower"],
        "ci_95_upper": posterior["ci_95_upper"],
        "bias": bias,
        "within_95ci": within_ci,
        "residual_pct": abs(bias) * 100,
    }


def run_literature_validation(
    vaccine_type: str,
    validation_data_path: Union[str, Path],
    n_mc_samples: int = 5_000,
    seed: int = 42,
) -> pd.DataFrame:
    """Validate against all rows in a stability CSV file.

    Parameters
    ----------
    vaccine_type : str
        Key into VACCINE_DB.
    validation_data_path : str or Path
        Path to the stability CSV (columns: temperature_C, duration_hours,
        measured_potency, plus optional metadata).
    n_mc_samples : int
    seed : int

    Returns
    -------
    pd.DataFrame
        One row per validation point with predicted and observed values.
    """
    params = VACCINE_DB[vaccine_type]
    df = pd.read_csv(validation_data_path)
    rng = np.random.default_rng(seed)

    records = []
    for _, row in df.iterrows():
        result = validate_single_point(
            temperature_C=float(row["temperature_C"]),
            duration_hours=float(row["duration_hours"]),
            measured_potency=float(row["measured_potency"]),
            vaccine_params=params,
            n_mc_samples=n_mc_samples,
            rng=rng,
        )
        result["source_citation"] = row.get("source_citation", "")
        result["assay_method"] = row.get("assay_method", "")
        records.append(result)

    return pd.DataFrame(records)
