"""Smoke tests for the ColdGuard CLI over every bundled scenario."""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
CSVS = sorted((ROOT / "data" / "raw").glob("*.csv"))


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(ROOT / "coldguard_cli.py"), *args],
        capture_output=True, text=True, cwd=ROOT, env={"PYTHONPATH": str(ROOT), "PATH": ""},
    )


def test_logging_gap_does_not_crash():
    r = run_cli("-i", "data/raw/logging_gap.csv", "-v", "DPT", "--samples", "200")
    assert r.returncode == 0, r.stderr
    assert "Logging gaps" in r.stdout


def test_all_vaccines_accepted():
    r = run_cli("-i", "data/raw/normal_cold_storage.csv", "-v", "JE", "--samples", "200")
    assert r.returncode == 0, r.stderr


@pytest.mark.parametrize("csv", CSVS, ids=lambda p: p.name)
def test_every_scenario_runs(csv):
    r = run_cli("-i", str(csv), "-v", "DPT", "--samples", "200")
    assert r.returncode == 0, r.stderr


def test_json_output_is_clean_and_decision_is_a_string():
    import json
    r = run_cli("-i", "data/raw/normal_cold_storage.csv", "-v", "DPT", "--samples", "200",
                "--seed", "1", "--json")
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["decision_output"]["decision"] in {"USE", "INVESTIGATE", "DISCARD"}
    assert "__objclass__" not in r.stdout
