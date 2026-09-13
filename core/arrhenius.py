"""
Arrhenius kinetic model for vaccine thermostability.

All public functions accept temperatures in Celsius and timestamps as Unix
seconds, but internally work with Kelvin and hours.
"""

from __future__ import annotations

import math
from typing import List, Dict, Any

import numpy as np

from .vaccine_params import R_GAS, VaccineParams


# ---------------------------------------------------------------------------
# Low-level kinetics
# ---------------------------------------------------------------------------

def arrhenius_k(T_kelvin: float, Ea: float, A: float) -> float:
    """Return the first-order rate constant k at temperature T_kelvin.

    Parameters
    ----------
    T_kelvin : float
        Absolute temperature in Kelvin.
    Ea : float
        Activation energy in J/mol.
    A : float
        Pre-exponential factor in hr^-1.

    Returns
    -------
    float
        Rate constant k in hr^-1.
    """
    return A * math.exp(-Ea / (R_GAS * T_kelvin))


def integrate_degradation(
    timestamps: np.ndarray,
    temperatures_C: np.ndarray,
    Ea: float,
    A: float,
) -> float:
    """Integrate k(T) dt using the trapezoidal rule.

    Parameters
    ----------
    timestamps : array-like
        Unix timestamps in seconds.  Length N.
    temperatures_C : array-like
        Temperature readings in °C, one per timestamp.  Length N.
    Ea : float
        Activation energy in J/mol.
    A : float
        Pre-exponential factor in hr^-1.

    Returns
    -------
    float
        Cumulative degradation D (dimensionless, same units as A·t).
    """
    ts = np.asarray(timestamps, dtype=float)
    tc = np.asarray(temperatures_C, dtype=float)

    if len(ts) < 2:
        return 0.0

    k_vals = np.array([arrhenius_k(t + 273.15, Ea, A) for t in tc])

    # dt in hours (timestamps are seconds)
    dt_hours = np.diff(ts) / 3600.0

    # trapezoidal: average k at endpoints × interval
    k_avg = 0.5 * (k_vals[:-1] + k_vals[1:])
    D = float(np.sum(k_avg * dt_hours))
    return D


def compute_potency(
    timestamps: np.ndarray,
    temperatures_C: np.ndarray,
    Ea: float,
    A: float,
    initial_potency: float = 1.0,
) -> float:
    """Compute remaining potency as a fraction of initial_potency.

    Uses first-order kinetics: P = P0 * exp(-D).

    Returns
    -------
    float
        Potency fraction in [0, 1].
    """
    D = integrate_degradation(timestamps, temperatures_C, Ea, A)
    return float(initial_potency * math.exp(-D))


def compute_segment_attribution(
    timestamps: np.ndarray,
    temperatures_C: np.ndarray,
    Ea: float,
    A: float,
) -> List[Dict[str, Any]]:
    """Return per-segment contribution to total degradation.

    Each segment is the trapezoid between two consecutive readings.

    Returns
    -------
    list of dict
        Keys: start_ts, end_ts, start_temp_C, end_temp_C, duration_hours,
              mean_temp_C, degradation_contribution, degradation_fraction.
    """
    ts = np.asarray(timestamps, dtype=float)
    tc = np.asarray(temperatures_C, dtype=float)

    if len(ts) < 2:
        return []

    k_vals = np.array([arrhenius_k(t + 273.15, Ea, A) for t in tc])
    dt_hours = np.diff(ts) / 3600.0
    k_avg = 0.5 * (k_vals[:-1] + k_vals[1:])
    seg_D = k_avg * dt_hours
    total_D = float(np.sum(seg_D))

    segments = []
    for i in range(len(ts) - 1):
        frac = float(seg_D[i] / total_D) if total_D > 0 else 0.0
        segments.append(
            {
                "start_ts": float(ts[i]),
                "end_ts": float(ts[i + 1]),
                "start_temp_C": float(tc[i]),
                "end_temp_C": float(tc[i + 1]),
                "duration_hours": float(dt_hours[i]),
                "mean_temp_C": float(0.5 * (tc[i] + tc[i + 1])),
                "degradation_contribution": float(seg_D[i]),
                "degradation_fraction": frac,
            }
        )
    return segments


# ---------------------------------------------------------------------------
# WHO Mean Kinetic Temperature
# ---------------------------------------------------------------------------

def compute_mkt(temperatures_C: np.ndarray, Ea: float = 83_000) -> float:
    """Compute WHO Mean Kinetic Temperature (MKT) per ISO 11135.

    MKT = -Ea/R / ln( mean(exp(-Ea/(R*Ti))) )

    Parameters
    ----------
    temperatures_C : array-like
        Temperature readings in °C.
    Ea : float
        Activation energy in J/mol (default 83 000, typical for DPT).

    Returns
    -------
    float
        MKT in °C.
    """
    tc = np.asarray(temperatures_C, dtype=float)
    T_K = tc + 273.15
    exponents = np.exp(-Ea / (R_GAS * T_K))
    mean_exp = float(np.mean(exponents))
    if mean_exp <= 0:
        raise ValueError("mean_exp is non-positive; check temperature inputs")
    mkt_K = -Ea / (R_GAS * math.log(mean_exp))
    return mkt_K - 273.15


def mkt_potency_estimate(
    timestamps: np.ndarray,
    temperatures_C: np.ndarray,
    vaccine_params: VaccineParams,
) -> float:
    """Estimate potency using a single MKT-equivalent exposure.

    Computes MKT, then treats the full duration as isothermal at MKT.

    Returns
    -------
    float
        Potency fraction in [0, 1].
    """
    tc = np.asarray(temperatures_C, dtype=float)
    ts = np.asarray(timestamps, dtype=float)
    mkt_C = compute_mkt(tc, Ea=vaccine_params.Ea_mean)
    duration_hours = (ts[-1] - ts[0]) / 3600.0
    k_mkt = arrhenius_k(mkt_C + 273.15, vaccine_params.Ea_mean, vaccine_params.A)
    D = k_mkt * duration_hours
    return math.exp(-D)


# ---------------------------------------------------------------------------
# Parameter derivation
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Freeze damage accumulator
# ---------------------------------------------------------------------------

# First-order rate constant for freeze-induced potency loss (hr^-1).
# Based on WHO/GPV/98.07: freeze-sensitive vaccines lose ~40% potency per hour
# of freeze exposure at or below 0°C.
_FREEZE_DAMAGE_RATE = 0.5  # hr^-1


def compute_freeze_damage_fraction(
    timestamps: np.ndarray,
    temperatures_C: np.ndarray,
    vaccine_params: VaccineParams,
    freeze_threshold_C: float = 0.0,
) -> float:
    """Compute the potency retention factor due to freeze exposure.

    For non-freeze-sensitive vaccines returns 1.0 (no freeze damage).
    For freeze-sensitive vaccines applies first-order freeze kinetics:
    ``retention = exp(-k_freeze * total_freeze_hours)``.

    Parameters
    ----------
    timestamps : array-like
        Unix timestamps in seconds.
    temperatures_C : array-like
        Temperature readings in °C.
    vaccine_params : VaccineParams
        Must have ``freeze_sensitive`` attribute.
    freeze_threshold_C : float
        Temperature below which freeze damage is accumulated. Default 0.0°C.

    Returns
    -------
    float
        Retained potency fraction in [0, 1] attributable to freeze damage only.
        Multiply with thermal degradation potency for the combined estimate.
    """
    if not vaccine_params.freeze_sensitive:
        return 1.0

    tc = np.asarray(temperatures_C, dtype=float)
    ts = np.asarray(timestamps, dtype=float)

    if len(ts) < 2:
        return 1.0

    frozen = tc < freeze_threshold_C
    if not np.any(frozen):
        return 1.0

    # Accumulate time (hours) in segments where at least one endpoint is frozen
    dt_hours = np.diff(ts) / 3600.0
    segment_frozen = frozen[:-1] | frozen[1:]
    total_freeze_hours = float(np.sum(dt_hours[segment_frozen]))

    return float(math.exp(-_FREEZE_DAMAGE_RATE * total_freeze_hours))


def derive_A_from_shelf_life(
    shelf_life_hours: float,
    T_ref_C: float,
    min_potency: float,
    Ea: float,
) -> float:
    """Back-calculate A from shelf-life specification.

    Given that P = exp(-A*exp(-Ea/(R*T))*t) = min_potency after shelf_life_hours
    at temperature T_ref_C, solve for A.

    Returns
    -------
    float
        Pre-exponential factor A in hr^-1.
    """
    T_K = T_ref_C + 273.15
    # P = exp(-A * exp(-Ea/(R*T)) * t) = min_potency
    # => -A * exp(-Ea/(R*T)) * t = ln(min_potency)
    # => A = -ln(min_potency) / (exp(-Ea/(R*T)) * t)
    boltzmann = math.exp(-Ea / (R_GAS * T_K))
    A = -math.log(min_potency) / (boltzmann * shelf_life_hours)
    return A
