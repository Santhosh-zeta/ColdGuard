"""End-to-end tests: run all 10 synthetic scenarios through the full pipeline."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
import pytest

from core.utils import parse_csv_log, run_analysis
from core.decision import Decision

DATA_DIR = Path(__file__).parent.parent / "data" / "raw"

SCENARIOS = [
    ("normal_cold_storage.csv",    "DPT", Decision.USE,     0.990),
    ("brief_excursion_15c.csv",    "DPT", Decision.USE,     0.95),
    ("extended_excursion_25c.csv", "DPT", None,             0.80),  # decision varies
    ("multiple_excursions.csv",    "DPT", None,             0.80),
    ("near_freeze.csv",            "DPT", Decision.USE,     0.98),
    ("logging_gap.csv",            "DPT", None,             None),  # gap warning expected
    ("transport_scenario.csv",     "DPT", None,             0.90),
    ("outreach_scenario.csv",      "OPV", None,             None),  # OPV very sensitive
    ("freeze_event.csv",           "DPT", None,             None),  # freeze flagged
    ("worst_case.csv",             "DPT", None,             None),  # should be DISCARD
]


@pytest.mark.parametrize("filename,vaccine,expected_decision,min_potency", SCENARIOS)
def test_scenario_runs_without_error(filename, vaccine, expected_decision, min_potency):
    path = DATA_DIR / filename
    if not path.exists():
        pytest.skip(f"Scenario file not found: {filename}")
    ts, temps = parse_csv_log(path)
    result = run_analysis(vaccine, ts, temps, n_mc_samples=500)

    assert "decision_output" in result
    assert "posterior_summary" in result
    d = result["decision_output"]
    p = result["posterior_summary"]

    # Decision must be a valid Decision enum member
    assert d.decision in (Decision.USE, Decision.INVESTIGATE, Decision.DISCARD)

    # Potency must be in [0, 1]
    assert 0.0 <= p["mean"] <= 1.0

    # CI must be ordered
    assert p["ci_90_lower"] <= p["mean"] <= p["ci_90_upper"]

    # Check expected decision if specified
    if expected_decision is not None:
        assert d.decision == expected_decision, (
            f"{filename}: expected {expected_decision.value}, "
            f"got {d.decision.value} (potency={p['mean']*100:.1f}%)"
        )

    # Check minimum potency bound if specified
    if min_potency is not None:
        assert p["mean"] >= min_potency, (
            f"{filename}: potency {p['mean']*100:.1f}% below expected minimum "
            f"{min_potency*100:.0f}%"
        )


def test_worst_case_scenario_not_use():
    """48 hours at 20°C must not produce a confident USE decision for OPV."""
    path = DATA_DIR / "worst_case.csv"
    if not path.exists():
        pytest.skip("worst_case.csv not found")
    ts, temps = parse_csv_log(path)
    result = run_analysis("OPV", ts, temps, n_mc_samples=1000)
    d = result["decision_output"].decision
    # OPV has high uncertainty; at minimum it must not say USE
    assert d in (Decision.INVESTIGATE, Decision.DISCARD), (
        f"Expected INVESTIGATE or DISCARD for worst-case OPV, got {d.value}"
    )


def test_logging_gap_generates_warning():
    """logging_gap.csv should produce at least one data quality warning."""
    path = DATA_DIR / "logging_gap.csv"
    if not path.exists():
        pytest.skip("logging_gap.csv not found")
    ts, temps = parse_csv_log(path)
    result = run_analysis("DPT", ts, temps, n_mc_samples=200)
    # Either a logging gap warning or a gap detected
    has_warning = (
        len(result.get("data_quality_warnings", [])) > 0
        or len(result.get("logging_gaps", [])) > 0
    )
    assert has_warning, "Expected gap warning but none found"


def test_freeze_event_detected():
    """freeze_event.csv should detect a freeze for freeze-sensitive vaccines."""
    path = DATA_DIR / "freeze_event.csv"
    if not path.exists():
        pytest.skip("freeze_event.csv not found")
    ts, temps = parse_csv_log(path)
    result = run_analysis("DPT", ts, temps, n_mc_samples=200)
    freeze_events = result.get("freeze_events", [])
    assert len(freeze_events) > 0, "Expected freeze event detected for freeze_event.csv"
