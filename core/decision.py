"""
Decision engine: translates a potency posterior into an actionable recommendation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Tuple

from .vaccine_params import VaccineParams


class Decision(Enum):
    """Tri-state recommendation for vaccine batch disposition."""
    USE = "USE"
    INVESTIGATE = "INVESTIGATE"
    DISCARD = "DISCARD"


@dataclass
class DecisionOutput:
    """Full structured output of the decision engine."""

    decision: Decision
    confidence: float                        # P(potency > threshold)
    estimated_potency_pct: float             # posterior mean × 100
    ci_90: Tuple[float, float]               # (lower, upper) percentiles × 100
    primary_degradation_cause: str           # human-readable root cause
    natural_language_explanation: str        # paragraph for health worker
    audit_hash: str                          # SHA-256 of posterior_summary


# ---------------------------------------------------------------------------
# Core decision logic
# ---------------------------------------------------------------------------

def make_decision(
    posterior_summary: Dict[str, float],
    vaccine_params: VaccineParams,
    segment_attribution: List[Dict[str, Any]],
) -> DecisionOutput:
    """Translate a Monte-Carlo posterior into a decision.

    Thresholds
    ----------
    P(potency > min_threshold) > 0.90  → USE
    P(potency > min_threshold) > 0.70  → INVESTIGATE
    else                                → DISCARD

    Parameters
    ----------
    posterior_summary : dict
        Output of compute_posterior_summary.
    vaccine_params : VaccineParams
        Parameters for the vaccine under assessment.
    segment_attribution : list of dict
        Per-segment degradation from compute_segment_attribution.

    Returns
    -------
    DecisionOutput
    """
    threshold = vaccine_params.min_potency_threshold

    # Probability above threshold
    if threshold >= 0.80:
        p_ok = posterior_summary["prob_above_80pct"]
    elif threshold >= 0.67:
        p_ok = posterior_summary["prob_above_67pct"]
    else:
        # Fallback: compute from mean/std approximation
        from scipy import stats  # local import to avoid hard dep at module level
        mean = posterior_summary["mean"]
        std = posterior_summary["std"]
        p_ok = float(1.0 - stats.norm.cdf(threshold, loc=mean, scale=std))

    if p_ok > 0.90:
        decision = Decision.USE
    elif p_ok > 0.70:
        decision = Decision.INVESTIGATE
    else:
        decision = Decision.DISCARD

    primary_cause = _identify_primary_cause(segment_attribution)
    explanation = _generate_explanation(decision, posterior_summary, primary_cause, vaccine_params)
    audit_hash = _compute_audit_hash(posterior_summary)

    return DecisionOutput(
        decision=decision,
        confidence=float(p_ok),
        estimated_potency_pct=float(posterior_summary["mean"] * 100),
        ci_90=(
            float(posterior_summary["ci_90_lower"] * 100),
            float(posterior_summary["ci_90_upper"] * 100),
        ),
        primary_degradation_cause=primary_cause,
        natural_language_explanation=explanation,
        audit_hash=audit_hash,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _identify_primary_cause(segment_attribution: List[Dict[str, Any]]) -> str:
    """Return a plain-language description of the segment with most degradation."""
    if not segment_attribution:
        return "Insufficient data to identify cause."

    worst = max(segment_attribution, key=lambda s: s["degradation_contribution"])
    temp = worst["mean_temp_C"]
    dur = worst["duration_hours"]
    frac = worst["degradation_fraction"] * 100

    if temp > 25:
        category = "high-temperature excursion"
    elif temp > 15:
        category = "moderate-temperature excursion"
    elif temp > 8:
        category = "mild elevated temperature"
    elif temp < 0:
        category = "freeze event"
    else:
        category = "normal cold-chain storage"

    return (
        f"{category.capitalize()} ({temp:.1f}°C for {dur:.1f} h), "
        f"accounting for {frac:.1f}% of total degradation"
    )


def _generate_explanation(
    decision: Decision,
    summary: Dict[str, float],
    cause: str,
    params: VaccineParams,
) -> str:
    """Return a plain-language explanation suitable for a health worker."""
    mean_pct = summary["mean"] * 100
    lo_pct = summary["ci_90_lower"] * 100
    hi_pct = summary["ci_90_upper"] * 100
    thresh_pct = params.min_potency_threshold * 100

    preamble = (
        f"ColdGuard estimates {params.name} potency at "
        f"{mean_pct:.1f}% (90% CI: {lo_pct:.1f}–{hi_pct:.1f}%). "
        f"The minimum acceptable potency for this vaccine is {thresh_pct:.0f}%. "
        f"The primary source of degradation was: {cause}. "
    )

    if decision is Decision.USE:
        action = (
            "Based on the temperature history, there is a high probability that "
            "this batch remains above the minimum potency threshold. "
            "It is safe to USE this vaccine."
        )
    elif decision is Decision.INVESTIGATE:
        action = (
            "There is some uncertainty about whether this batch remains potent. "
            "Please INVESTIGATE further: check the VVM indicator, inspect the vial "
            "visually, and consult your cold-chain supervisor before administration."
        )
    else:  # DISCARD
        action = (
            "The temperature history indicates substantial degradation. "
            "This batch is likely below the minimum potency threshold. "
            "Please DISCARD and do not administer to patients."
        )

    return preamble + action


def _compute_audit_hash(posterior_summary: Dict[str, float]) -> str:
    """Return a SHA-256 hex digest of the serialised posterior summary."""
    serialised = json.dumps(posterior_summary, sort_keys=True, default=str)
    return hashlib.sha256(serialised.encode("utf-8")).hexdigest()
