"""
Calibration analysis for the ColdGuard Bayesian model.

Computes:
- Coverage probability (fraction of measured values within predicted CI)
- RMSE and MAE between predicted means and observed values
- Bland-Altman agreement analysis
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Tuple, Union

import numpy as np
import pandas as pd


def coverage_probability(results_df: pd.DataFrame, ci_level: str = "95") -> float:
    """Compute fraction of observed values that fall within the predicted CI.

    Parameters
    ----------
    results_df : pd.DataFrame
        Output of run_literature_validation (must have columns
        ci_95_lower/ci_95_upper or ci_90_lower/ci_90_upper and measured_potency).
    ci_level : str
        "90" or "95".

    Returns
    -------
    float
        Coverage probability in [0, 1].
    """
    if ci_level == "95":
        lo_col, hi_col = "ci_95_lower", "ci_95_upper"
    else:
        lo_col, hi_col = "ci_90_lower", "ci_90_upper"

    obs = results_df["measured_potency"].values
    lo = results_df[lo_col].values
    hi = results_df[hi_col].values
    inside = (obs >= lo) & (obs <= hi)
    return float(np.mean(inside))


def rmse(results_df: pd.DataFrame) -> float:
    """Root Mean Square Error between mc_mean and measured_potency."""
    obs = results_df["measured_potency"].values
    pred = results_df["mc_mean"].values
    return float(np.sqrt(np.mean((pred - obs) ** 2)))


def mae(results_df: pd.DataFrame) -> float:
    """Mean Absolute Error between mc_mean and measured_potency."""
    obs = results_df["measured_potency"].values
    pred = results_df["mc_mean"].values
    return float(np.mean(np.abs(pred - obs)))


def bland_altman(
    results_df: pd.DataFrame,
) -> Dict[str, Any]:
    """Bland-Altman analysis (limits of agreement).

    Returns
    -------
    dict with keys:
        mean_bias, std_diff, loa_upper, loa_lower, mean_mean
    """
    obs = results_df["measured_potency"].values
    pred = results_df["mc_mean"].values
    diffs = pred - obs
    means = 0.5 * (pred + obs)

    mean_bias = float(np.mean(diffs))
    std_diff = float(np.std(diffs, ddof=1))
    loa_upper = mean_bias + 1.96 * std_diff
    loa_lower = mean_bias - 1.96 * std_diff

    return {
        "mean_bias": mean_bias,
        "std_diff": std_diff,
        "loa_upper": loa_upper,
        "loa_lower": loa_lower,
        "mean_mean": float(np.mean(means)),
    }


def run_calibration_analysis(
    results_df: pd.DataFrame,
) -> Dict[str, Any]:
    """Run all calibration metrics on a validation results DataFrame.

    Parameters
    ----------
    results_df : pd.DataFrame
        Output of run_literature_validation.

    Returns
    -------
    dict
    """
    cov_95 = coverage_probability(results_df, ci_level="95")
    rmse_val = rmse(results_df)
    mae_val = mae(results_df)
    ba = bland_altman(results_df)

    return {
        "n_data_points": len(results_df),
        "coverage_probability_95ci": cov_95,
        "expected_coverage_95ci": 0.95,
        "coverage_adequate": cov_95 >= 0.90,
        "rmse": rmse_val,
        "mae": mae_val,
        "bland_altman": ba,
        "model_adequate": rmse_val < 0.05,
    }


if __name__ == "__main__":
    import sys
    import json

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from validation.literature_validation import run_literature_validation

    for vaccine, csv_name in [
        ("DPT", "dpt_stability.csv"),
        ("OPV", "opv_stability.csv"),
        ("MMR", "measles_stability.csv"),
    ]:
        csv_path = Path(__file__).parent.parent / "data" / "validation" / csv_name
        results = run_literature_validation(vaccine, csv_path, n_mc_samples=2000)
        cal = run_calibration_analysis(results)
        print(f"\n=== {vaccine} ===")
        print(json.dumps(cal, indent=2))
