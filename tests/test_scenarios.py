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


def test_yf_vaccine_normal_storage():
    """Yellow Fever in normal cold storage should produce a USE decision."""
    path = DATA_DIR / "yf_normal_storage.csv"
    if not path.exists():
        pytest.skip("yf_normal_storage.csv not found")
    ts, temps = parse_csv_log(path)
    result = run_analysis("YF", ts, temps, n_mc_samples=500)
    d = result["decision_output"]
    p = result["posterior_summary"]
    assert d.decision == Decision.USE, (
        f"Expected USE for YF normal storage, got {d.decision.value} "
        f"(potency={p['mean']*100:.1f}%)"
    )
    assert p["mean"] >= 0.97, f"YF potency {p['mean']*100:.1f}% too low for 3-day normal storage"


def test_freeze_damage_accumulator_reduces_potency():
    """Freeze damage must reduce point-estimate potency for freeze-sensitive vaccines."""
    import numpy as np
    from core.arrhenius import compute_freeze_damage_fraction
    from core.vaccine_params import VACCINE_DB

    # 2 hours below 0°C for DPT (freeze-sensitive)
    ts = np.array([0, 3600, 7200], dtype=float)  # 0, 1h, 2h
    temps = np.array([-3.0, -2.0, -1.5], dtype=float)  # all below 0
    dpt = VACCINE_DB["DPT"]
    retention = compute_freeze_damage_fraction(ts, temps, dpt)
    assert retention < 1.0, "Freeze-sensitive DPT should have retention < 1.0 when frozen"
    assert retention > 0.0, "Retention should be positive"

    # YF is not freeze-sensitive — no penalty
    yf = VACCINE_DB["YF"]
    retention_yf = compute_freeze_damage_fraction(ts, temps, yf)
    assert retention_yf == 1.0, "Non-freeze-sensitive YF should have retention == 1.0"


def test_je_vaccine_normal_storage():
    """Japanese Encephalitis in normal cold storage should produce a USE decision."""
    path = DATA_DIR / "je_normal_storage.csv"
    if not path.exists():
        pytest.skip("je_normal_storage.csv not found")
    ts, temps = parse_csv_log(path)
    result = run_analysis("JE", ts, temps, n_mc_samples=500)
    d = result["decision_output"]
    p = result["posterior_summary"]
    assert d.decision == Decision.USE, (
        f"Expected USE for JE normal storage, got {d.decision.value} "
        f"(potency={p['mean']*100:.1f}%)"
    )
    assert p["mean"] >= 0.97, f"JE potency {p['mean']*100:.1f}% too low for 3-day normal storage"


def test_freeze_damage_reflected_in_run_analysis():
    """run_analysis on freeze_event.csv for DPT should include freeze_damage_retention < 1."""
    path = DATA_DIR / "freeze_event.csv"
    if not path.exists():
        pytest.skip("freeze_event.csv not found")
    ts, temps = parse_csv_log(path)
    result = run_analysis("DPT", ts, temps, n_mc_samples=200)
    fdr = result.get("freeze_damage_retention")
    assert fdr is not None, "run_analysis must return freeze_damage_retention"
    assert fdr < 1.0, f"Expected freeze damage retention < 1.0 for freeze event, got {fdr}"
