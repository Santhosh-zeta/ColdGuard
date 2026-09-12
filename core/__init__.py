"""
ColdGuard core package.

Public API
----------
run_analysis(vaccine_type, timestamps, temperatures_C, ...) → dict
VACCINE_DB  – dict mapping vaccine codes to VaccineParams
Decision    – USE / INVESTIGATE / DISCARD enum
DecisionOutput – dataclass returned by make_decision
"""

from .vaccine_params import VACCINE_DB, VaccineParams, R_GAS
from .arrhenius import (
    arrhenius_k,
    compute_potency,
    integrate_degradation,
    compute_segment_attribution,
    compute_mkt,
    mkt_potency_estimate,
    derive_A_from_shelf_life,
)
from .bayesian import monte_carlo_potency_distribution, compute_posterior_summary
from .decision import Decision, DecisionOutput, make_decision
from .utils import (
    parse_csv_log,
    parse_json_log,
    validate_temperature_log,
    detect_freeze_events,
    detect_logging_gaps,
    run_analysis,
)

__all__ = [
    "VACCINE_DB",
    "VaccineParams",
    "R_GAS",
    "arrhenius_k",
    "compute_potency",
    "integrate_degradation",
    "compute_segment_attribution",
    "compute_mkt",
    "mkt_potency_estimate",
    "derive_A_from_shelf_life",
    "monte_carlo_potency_distribution",
    "compute_posterior_summary",
    "Decision",
    "DecisionOutput",
    "make_decision",
    "parse_csv_log",
    "parse_json_log",
    "validate_temperature_log",
    "detect_freeze_events",
    "detect_logging_gaps",
    "run_analysis",
]
