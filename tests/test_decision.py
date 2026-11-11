"""Tests for core.decision — decision support engine."""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pytest

from core.bayesian import compute_posterior_summary
from core.decision import Decision, DecisionOutput, make_decision
from core.vaccine_params import VACCINE_DB
from core.utils import parse_csv_log, run_analysis


@pytest.fixture
def dpt():
    return VACCINE_DB["DPT"]


def _make_summary(high_potency: bool):
    """Return a synthetic posterior summary with controlled potency level."""
    if high_potency:
        # 99% potency → should be USE
        samples = np.random.uniform(0.97, 1.00, 5000)
    else:
        # 60% potency → should be DISCARD
        samples = np.random.uniform(0.55, 0.65, 5000)
    return compute_posterior_summary(samples)


def _empty_attribution():
    return []


def test_high_potency_gives_use_decision(dpt):
    summary = _make_summary(high_potency=True)
    result = make_decision(summary, dpt, _empty_attribution())
    assert result.decision == Decision.USE


def test_low_potency_gives_discard_decision(dpt):
    summary = _make_summary(high_potency=False)
    result = make_decision(summary, dpt, _empty_attribution())
    assert result.decision == Decision.DISCARD


def test_investigate_for_borderline(dpt):
    # Build a distribution where P(>0.80) is between 0.70 and 0.90
    samples = np.concatenate(
        [
            np.random.uniform(0.81, 0.95, 4000),  # above threshold
            np.random.uniform(0.60, 0.80, 3000),  # below threshold
        ]
    )
    summary = compute_posterior_summary(samples)
    result = make_decision(summary, dpt, _empty_attribution())
    assert result.decision in (Decision.INVESTIGATE, Decision.DISCARD, Decision.USE)


def test_decision_output_has_all_fields(dpt):
    summary = _make_summary(high_potency=True)
    result = make_decision(summary, dpt, _empty_attribution())
    assert isinstance(result, DecisionOutput)
    assert hasattr(result, "decision")
    assert hasattr(result, "confidence")
    assert hasattr(result, "estimated_potency_pct")
    assert hasattr(result, "ci_90")
    assert hasattr(result, "primary_degradation_cause")
    assert hasattr(result, "natural_language_explanation")
    assert hasattr(result, "audit_hash")


def test_audit_hash_is_nonempty_string(dpt):
    summary = _make_summary(high_potency=True)
    result = make_decision(summary, dpt, _empty_attribution())
    assert isinstance(result.audit_hash, str)
    assert len(result.audit_hash) > 0


def test_explanation_contains_vaccine_name(dpt):
    summary = _make_summary(high_potency=True)
    result = make_decision(summary, dpt, _empty_attribution())
    assert (
        "DPT" in result.natural_language_explanation
        or "Diphtheria" in result.natural_language_explanation
    )


def test_estimated_potency_pct_in_valid_range(dpt):
    summary = _make_summary(high_potency=True)
    result = make_decision(summary, dpt, _empty_attribution())
    assert 0.0 <= result.estimated_potency_pct <= 100.0


def test_ci_90_tuple_ordered(dpt):
    summary = _make_summary(high_potency=True)
    result = make_decision(summary, dpt, _empty_attribution())
    lo, hi = result.ci_90
    assert lo <= hi


def test_decision_uses_exact_threshold_probability():
    """A custom threshold must drive P(ok) rather than the 0.80/0.67 buckets."""
    import numpy as np
    from core.vaccine_params import VACCINE_DB
    from dataclasses import replace

    samples = np.full(1000, 0.85)
    summary = compute_posterior_summary(samples, threshold=0.90)
    assert summary["prob_above_threshold"] == 0.0
    params = replace(VACCINE_DB["DPT"], min_potency_threshold=0.90)
    out = make_decision(summary, params, [])
    assert out.decision.name == "DISCARD"


@pytest.mark.parametrize("vaccine", ["DPT", "HepB"])
def test_freeze_event_explanation_names_freeze_damage(vaccine):
    path = Path(__file__).parent.parent / "data" / "raw" / "freeze_event.csv"
    timestamps, temperatures = parse_csv_log(path)
    result = run_analysis(vaccine, timestamps, temperatures, n_mc_samples=500, seed=143)
    output = result["decision_output"]

    assert output.decision is Decision.DISCARD
    assert output.primary_degradation_cause.startswith("Freeze exposure")
    assert "min -5.0°C" in output.primary_degradation_cause
    assert "3.0 h" in output.primary_degradation_cause
    freeze_loss_pct = (1.0 - result["freeze_damage_retention"]) * 100
    assert f"{freeze_loss_pct:.1f}%" in output.primary_degradation_cause
    assert output.primary_degradation_cause in output.natural_language_explanation
    assert "Normal cold-chain storage" not in output.natural_language_explanation


@pytest.mark.parametrize("filename", ["normal_cold_storage.csv", "worst_case.csv"])
def test_thermal_only_explanation_is_unchanged(filename):
    path = Path(__file__).parent.parent / "data" / "raw" / filename
    timestamps, temperatures = parse_csv_log(path)
    result = run_analysis("DPT", timestamps, temperatures, n_mc_samples=500, seed=143)
    legacy_output = make_decision(
        result["posterior_summary"], VACCINE_DB["DPT"], result["segment_attribution"]
    )

    assert not result["freeze_events"]
    assert result["decision_output"] == legacy_output


def test_heat_dominated_log_keeps_thermal_cause_despite_freeze_event():
    timestamps = np.array([0, 48 * 3600, 48 * 3600 + 60], dtype=float)
    temperatures = np.array([60, 60, -1], dtype=float)
    result = run_analysis("DPT", timestamps, temperatures, n_mc_samples=500, seed=143)
    legacy_output = make_decision(
        result["posterior_summary"], VACCINE_DB["DPT"], result["segment_attribution"]
    )

    assert result["freeze_events"]
    assert result["freeze_damage_retention"] < 1.0
    assert result["decision_output"] == legacy_output
    assert "High-temperature excursion" in legacy_output.primary_degradation_cause


def test_freeze_insensitive_vaccine_keeps_thermal_explanation():
    path = Path(__file__).parent.parent / "data" / "raw" / "freeze_event.csv"
    timestamps, temperatures = parse_csv_log(path)
    result = run_analysis("OPV", timestamps, temperatures, n_mc_samples=500, seed=143)
    legacy_output = make_decision(
        result["posterior_summary"], VACCINE_DB["OPV"], result["segment_attribution"]
    )

    assert result["freeze_events"]
    assert result["freeze_damage_retention"] == 1.0
    assert result["decision_output"] == legacy_output


def test_multiple_freeze_events_use_elapsed_intervals_not_reading_count():
    timestamps = np.array([0, 1800, 7200, 10800], dtype=float)
    temperatures = np.array([-2, 5, -4, 5], dtype=float)
    result = run_analysis("DPT", timestamps, temperatures, n_mc_samples=500, seed=143)
    cause = result["decision_output"].primary_degradation_cause

    assert len(result["freeze_events"]) == 2
    assert cause == (
        "Freeze exposure (min -4.0°C for 3.0 h), "
        "reducing potency by 77.7% through freeze damage"
    )


def test_freeze_loss_is_compared_to_total_thermal_loss(dpt):
    segments = [
        {
            "degradation_contribution": 0.3,
            "degradation_fraction": 0.5,
            "mean_temp_C": 40.0,
            "duration_hours": 1.0,
        }
        for _ in range(2)
    ]
    summary = _make_summary(high_potency=False)
    legacy_output = make_decision(summary, dpt, segments)
    output = make_decision(
        summary,
        dpt,
        segments,
        freeze_events=[{"min_temp_C": -5.0}],
        freeze_damage_retention=0.6,
    )

    # Combined thermal loss is 45.1%, even though each interval alone loses 25.9%.
    assert output == legacy_output
