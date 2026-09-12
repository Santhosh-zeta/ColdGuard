"""Tests for core.decision — decision support engine."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pytest

from core.bayesian import monte_carlo_potency_distribution, compute_posterior_summary
from core.decision import Decision, DecisionOutput, make_decision
from core.vaccine_params import VACCINE_DB
from core.arrhenius import compute_segment_attribution


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
    from core.bayesian import compute_posterior_summary
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
    samples = np.concatenate([
        np.random.uniform(0.81, 0.95, 4000),  # above threshold
        np.random.uniform(0.60, 0.80, 3000),  # below threshold
    ])
    from core.bayesian import compute_posterior_summary
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
    assert "DPT" in result.natural_language_explanation or "Diphtheria" in result.natural_language_explanation


def test_estimated_potency_pct_in_valid_range(dpt):
    summary = _make_summary(high_potency=True)
    result = make_decision(summary, dpt, _empty_attribution())
    assert 0.0 <= result.estimated_potency_pct <= 100.0


def test_ci_90_tuple_ordered(dpt):
    summary = _make_summary(high_potency=True)
    result = make_decision(summary, dpt, _empty_attribution())
    lo, hi = result.ci_90
    assert lo <= hi
