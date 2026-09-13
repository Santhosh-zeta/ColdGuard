"""Tests for core.arrhenius — kinetic degradation engine."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pytest

from core.arrhenius import (
    arrhenius_k,
    integrate_degradation,
    compute_potency,
    compute_mkt,
    derive_A_from_shelf_life,
    compute_segment_attribution,
)
from core.vaccine_params import VACCINE_DB


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def dpt():
    return VACCINE_DB["DPT"]


def _constant_log(temp_C: float, duration_hours: float, n: int = 10):
    """Create a constant-temperature time series."""
    ts = np.linspace(0, duration_hours * 3600, n)
    temps = np.full(n, temp_C)
    return ts, temps


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_arrhenius_k_positive(dpt):
    k = arrhenius_k(277.15, dpt.Ea_mean, dpt.A)
    assert k > 0


def test_arrhenius_k_increases_with_temperature(dpt):
    k_cold = arrhenius_k(277.15, dpt.Ea_mean, dpt.A)
    k_warm = arrhenius_k(310.15, dpt.Ea_mean, dpt.A)
    assert k_warm > k_cold


def test_integrate_degradation_constant_matches_analytic(dpt):
    """D = k(T) * t for constant temperature (analytic result)."""
    temp_C = 10.0
    duration_h = 100.0
    ts, temps = _constant_log(temp_C, duration_h, n=1000)
    D_numeric = integrate_degradation(ts, temps, dpt.Ea_mean, dpt.A)
    k_exact = arrhenius_k(temp_C + 273.15, dpt.Ea_mean, dpt.A)
    D_analytic = k_exact * duration_h
    assert abs(D_numeric - D_analytic) / D_analytic < 0.001  # within 0.1%


def test_potency_short_cold_storage_near_100(dpt):
    """4°C for 48 hours: potency should be essentially 100%."""
    ts, temps = _constant_log(4.0, 48.0)
    p = compute_potency(ts, temps, dpt.Ea_mean, dpt.A)
    assert p > 0.999


def test_potency_high_temp_long_duration_below_50pct():
    """OPV at 37°C for 240 hours (10 days): well below 50% potency."""
    opv = VACCINE_DB["OPV"]
    ts, temps = _constant_log(37.0, 240.0)
    p = compute_potency(ts, temps, opv.Ea_mean, opv.A)
    # OPV is extremely heat-sensitive: Ea=112kJ/mol, very large A
    assert p < 0.10


def test_hand_calculated_dpt_scenario(dpt):
    """DPT: 72h@4°C + 11h@14°C + 85h@4°C ≈ 99.8% potency (from project doc)."""
    # Build the time series: 1-hour resolution
    hours = [4.0] * 72 + [14.0] * 11 + [4.0] * 85
    n = len(hours) + 1
    ts = np.arange(n) * 3600.0
    temps = np.array(hours + [4.0])
    p = compute_potency(ts, temps, dpt.Ea_mean, dpt.A)
    # Doc says ~99.8%; with exact Ea_mean we expect > 99%
    assert p > 0.99


def test_mkt_formula(dpt):
    """MKT of a constant 5°C series must equal 5°C."""
    temps = np.full(100, 5.0)
    mkt = compute_mkt(temps, Ea=dpt.Ea_mean)
    assert abs(mkt - 5.0) < 0.01


def test_derive_A_from_shelf_life_round_trip(dpt):
    """A derived from shelf-life spec must reproduce the correct shelf-life potency."""
    A_derived = derive_A_from_shelf_life(
        shelf_life_hours=dpt.shelf_life_hours,
        T_ref_C=dpt.ref_temp_K - 273.15,
        min_potency=dpt.min_potency_threshold,
        Ea=dpt.Ea_mean,
    )
    # Verify: using A_derived, potency at end of shelf life should equal min_potency
    import numpy as np
    ts = np.array([0.0, dpt.shelf_life_hours * 3600.0])
    temps = np.array([dpt.ref_temp_K - 273.15, dpt.ref_temp_K - 273.15])
    p = compute_potency(ts, temps, dpt.Ea_mean, A_derived)
    assert abs(p - dpt.min_potency_threshold) < 0.005  # within 0.5 percentage points


def test_segment_attribution_sums_to_total(dpt):
    """Segment-level degradation fractions must sum to ~1.0."""
    ts = np.array([0, 72, 83, 168]) * 3600.0
    temps = np.array([4.0, 14.0, 14.0, 4.0])
    segs = compute_segment_attribution(ts, temps, dpt.Ea_mean, dpt.A)
    total_frac = sum(s["degradation_fraction"] for s in segs)
    assert abs(total_frac - 1.0) < 0.001
