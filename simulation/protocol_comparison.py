"""
Protocol comparison study: VVM-based vs MKT threshold vs ColdGuard.

Generates synthetic scenarios and evaluates three decision protocols,
computing False Discard Rate, False Use Rate, and Decision Accuracy.
"""

from __future__ import annotations

from typing import Dict, Any

import numpy as np

from .cold_chain_generator import (
    INDIA_DISTRICT,
    INDIA_PHC,
    INDIA_OUTREACH,
    generate_scenario,
)
from core.arrhenius import compute_potency, compute_mkt
from core.bayesian import monte_carlo_potency_distribution, compute_posterior_summary
from core.decision import make_decision, Decision
from core.vaccine_params import VACCINE_DB


# ---------------------------------------------------------------------------
# Decision protocol implementations
# ---------------------------------------------------------------------------

def _vvm_decision(temperatures_C: np.ndarray, vaccine_type: str) -> str:
    """Simplified VVM-based decision.

    A VVM advances when mean temperature exceeds 8°C for more than 10% of
    the total monitoring period.  If the VVM reaches stage 3 (irreversible
    change), the batch is discarded.
    """
    frac_above = float(np.mean(temperatures_C > 8.0))
    # Stage 3 threshold: >10% of time above 8°C (simplified heuristic)
    if frac_above > 0.10:
        return Decision.DISCARD.value
    elif frac_above > 0.05:
        return Decision.INVESTIGATE.value
    else:
        return Decision.USE.value


def _mkt_decision(
    timestamps: np.ndarray,
    temperatures_C: np.ndarray,
    vaccine_type: str,
) -> str:
    """MKT-based decision: discard if MKT > 8°C, investigate if 6–8°C."""
    params = VACCINE_DB[vaccine_type]
    mkt = compute_mkt(temperatures_C, Ea=params.Ea_mean)
    if mkt > 8.0:
        return Decision.DISCARD.value
    elif mkt > 6.0:
        return Decision.INVESTIGATE.value
    else:
        return Decision.USE.value


def _coldguard_decision(
    timestamps: np.ndarray,
    temperatures_C: np.ndarray,
    vaccine_type: str,
    rng: np.random.Generator,
) -> str:
    """Full ColdGuard Bayesian decision."""
    params = VACCINE_DB[vaccine_type]
    samples = monte_carlo_potency_distribution(
        timestamps, temperatures_C, params, n_samples=1000, rng=rng
    )
    posterior = compute_posterior_summary(samples)
    segments: list = []  # no segment detail needed for comparison
    decision_out = make_decision(posterior, params, segments)
    return decision_out.decision.value


# ---------------------------------------------------------------------------
# Ground-truth potency (deterministic point estimate)
# ---------------------------------------------------------------------------

def _ground_truth_decision(
    timestamps: np.ndarray,
    temperatures_C: np.ndarray,
    vaccine_type: str,
) -> str:
    """Point-estimate 'ground truth' using mean Ea and A."""
    params = VACCINE_DB[vaccine_type]
    potency = compute_potency(
        timestamps, temperatures_C, params.Ea_mean, params.A
    )
    if potency >= params.min_potency_threshold:
        return Decision.USE.value
    else:
        return Decision.DISCARD.value


# ---------------------------------------------------------------------------
# Comparison study
# ---------------------------------------------------------------------------

def run_comparison_study(
    n_scenarios: int = 1_000,
    vaccine_type: str = "DPT",
    seed: int = 42,
    total_duration_days: float = 7.0,
) -> Dict[str, Any]:
    """Run the full three-protocol comparison study.

    Parameters
    ----------
    n_scenarios : int
    vaccine_type : str
    seed : int
    total_duration_days : float

    Returns
    -------
    dict with keys: n_scenarios, vaccine_type, per_profile_results, overall_results
    """
    rng = np.random.default_rng(seed)
    profiles = [INDIA_DISTRICT, INDIA_PHC, INDIA_OUTREACH]
    profile_results: Dict[str, Dict[str, Any]] = {}

    for profile in profiles:
        vvm_decisions = []
        mkt_decisions = []
        cg_decisions = []
        gt_decisions = []

        n_each = n_scenarios // len(profiles)
        for _ in range(n_each):
            ts, tc = generate_scenario(profile, total_duration_days, rng)
            gt = _ground_truth_decision(ts, tc, vaccine_type)
            vvm = _vvm_decision(tc, vaccine_type)
            mkt = _mkt_decision(ts, tc, vaccine_type)
            cg = _coldguard_decision(ts, tc, vaccine_type, rng)

            gt_decisions.append(gt)
            vvm_decisions.append(vvm)
            mkt_decisions.append(mkt)
            cg_decisions.append(cg)

        def metrics(pred_list, gt_list):
            n = len(pred_list)
            tp = sum(
                p == Decision.USE.value and g == Decision.USE.value
                for p, g in zip(pred_list, gt_list)
            )
            fp = sum(
                p == Decision.USE.value and g == Decision.DISCARD.value
                for p, g in zip(pred_list, gt_list)
            )
            tn = sum(
                p == Decision.DISCARD.value and g == Decision.DISCARD.value
                for p, g in zip(pred_list, gt_list)
            )
            fn = sum(
                p == Decision.DISCARD.value and g == Decision.USE.value
                for p, g in zip(pred_list, gt_list)
            )
            accuracy = (tp + tn) / n if n > 0 else 0
            fdr = fn / (fn + tp + 1e-9)   # False Discard Rate = missed USEs
            fur = fp / (fp + tn + 1e-9)   # False Use Rate = missed DISCARDs
            return {
                "false_discard_rate": round(fdr, 4),
                "false_use_rate": round(fur, 4),
                "decision_accuracy": round(accuracy, 4),
                "n_true_good": tp + fn,
                "n_true_bad": fp + tn,
            }

        profile_results[profile.name] = {
            "vvm": metrics(vvm_decisions, gt_decisions),
            "mkt": metrics(mkt_decisions, gt_decisions),
            "coldguard": metrics(cg_decisions, gt_decisions),
        }

    # Aggregate across profiles
    def agg_metric(key):
        vals = [profile_results[p.name]["coldguard"][key] for p in profiles]
        return round(float(np.mean(vals)), 4)

    overall = {
        "coldguard_mean_accuracy": agg_metric("decision_accuracy"),
        "coldguard_mean_fdr": agg_metric("false_discard_rate"),
        "coldguard_mean_fur": agg_metric("false_use_rate"),
    }

    return {
        "n_scenarios": n_scenarios,
        "vaccine_type": vaccine_type,
        "per_profile_results": profile_results,
        "overall_results": overall,
    }


if __name__ == "__main__":
    import json

    print("Running protocol comparison study (n=200 for speed)...")
    results = run_comparison_study(n_scenarios=200, seed=42)
    print(json.dumps(results, indent=2))
