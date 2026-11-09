"""Smoke tests for the ColdGuard CLI over every bundled scenario."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

import coldguard_cli
from core import __version__

ROOT = Path(__file__).parent.parent
CSVS = sorted((ROOT / "data" / "raw").glob("*.csv"))


def run_cli(*args, env=None):
    run_env = {"PYTHONPATH": str(ROOT), "PATH": ""}
    if env:
        run_env.update(env)
    return subprocess.run(
        [sys.executable, str(ROOT / "coldguard_cli.py"), *args],
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT, env=run_env,
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
    assert "\x1b[" not in r.stdout


def test_json_output_is_clean_and_decision_is_a_string():
    r = run_cli("-i", "data/raw/normal_cold_storage.csv", "-v", "DPT", "--samples", "200",
                "--seed", "1", "--json")
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["decision_output"]["decision"] in {"USE", "INVESTIGATE", "DISCARD"}
    assert "__objclass__" not in r.stdout


def test_blank_reading_fails_with_a_clear_message(tmp_path):
    log = tmp_path / "blank_cell.csv"
    log.write_text(
        "timestamp,temperature_celsius\n0,5\n3600,\n7200,5\n", encoding="utf-8"
    )
    r = run_cli("-i", str(log), "-v", "DPT", "--samples", "200")
    assert r.returncode == 1
    assert "non-finite values at index 1 in temperatures_C" in r.stderr


def test_version_flag():
    r = run_cli("--version")
    assert r.returncode == 0, r.stderr
    assert __version__ in r.stdout
    assert "\x1b[" not in r.stdout


def test_piped_output_auto_disables_color():
    r = run_cli("-i", "data/raw/normal_cold_storage.csv", "-v", "DPT", "--samples", "200")
    assert r.returncode == 0, r.stderr
    assert "\x1b[" not in r.stdout


def test_no_color_flag():
    r = run_cli("-i", "data/raw/normal_cold_storage.csv", "-v", "DPT", "--samples", "200", "--no-color")
    assert r.returncode == 0, r.stderr
    assert "\x1b[" not in r.stdout


def test_no_color_env_var():
    r = run_cli("-i", "data/raw/normal_cold_storage.csv", "-v", "DPT", "--samples", "200",
                env={"NO_COLOR": "1"})
    assert r.returncode == 0, r.stderr
    assert "\x1b[" not in r.stdout


def test_tty_color_and_overrides(monkeypatch, capsys):
    csv_arg = str(ROOT / "data" / "raw" / "normal_cold_storage.csv")
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    monkeypatch.delenv("NO_COLOR", raising=False)

    monkeypatch.setattr(sys, "argv", ["coldguard_cli.py", "-i", csv_arg, "-v", "DPT", "--samples", "200"])
    coldguard_cli.main()
    assert "\x1b[" in capsys.readouterr().out

    monkeypatch.setattr(sys, "argv", ["coldguard_cli.py", "-i", csv_arg, "-v", "DPT", "--samples", "200", "--no-color"])
    coldguard_cli.main()
    assert "\x1b[" not in capsys.readouterr().out

    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setattr(sys, "argv", ["coldguard_cli.py", "-i", csv_arg, "-v", "DPT", "--samples", "200"])
    coldguard_cli.main()
    assert "\x1b[" not in capsys.readouterr().out


def test_validate_only_usable_csv_human_and_json():
    r = run_cli("-i", "data/raw/demo_dpt_power_outage.csv", "--validate-only")
    assert r.returncode == 0, r.stderr
    assert "VALID" in r.stdout
    assert "Readings" in r.stdout
    assert "Time span" in r.stdout
    assert "Sampling interval" in r.stdout
    assert "Min / max temperature" in r.stdout
    assert "\x1b[" not in r.stdout

    rj = run_cli("-i", "data/raw/demo_dpt_power_outage.csv", "--validate-only", "--json")
    assert rj.returncode == 0, rj.stderr
    data = json.loads(rj.stdout)
    assert data["usable"] is True
    assert data["num_readings"] == 17
    assert data["time_span_hours"] == pytest.approx(16.0)
    assert data["sampling_interval_minutes"] == pytest.approx(60.0)
    assert data["min_temp_C"] < data["max_temp_C"]
    assert data["logging_gaps"] == []
    assert data["freeze_events"] == []
    assert data["freeze_readings"] == 0
    assert data["non_increasing_timestamps"] == 0
    assert data["nan_values"] == 0
    assert data["errors"] == []


def test_validate_only_reports_gaps_and_freeze_events():
    r_gap = run_cli("-i", "data/raw/logging_gap.csv", "--validate-only", "--json")
    assert r_gap.returncode == 0, r_gap.stderr
    gap_data = json.loads(r_gap.stdout)
    assert gap_data["usable"] is True
    assert len(gap_data["logging_gaps"]) >= 1
    assert any("Logging gap" in w for w in gap_data["data_quality_warnings"])

    r_freeze = run_cli("-i", "data/raw/freeze_event.csv", "--validate-only", "--json")
    assert r_freeze.returncode == 0, r_freeze.stderr
    freeze_data = json.loads(r_freeze.stdout)
    assert freeze_data["usable"] is True
    assert len(freeze_data["freeze_events"]) >= 1
    assert freeze_data["freeze_readings"] >= 1
    assert freeze_data["min_temp_C"] < 0.0


def test_validate_only_rejects_unusable_csvs(tmp_path):
    # 1. NaN / blank value
    nan_csv = tmp_path / "nan.csv"
    nan_csv.write_text("timestamp,temperature_celsius\n0,4.0\n3600,\n7200,5.0\n", encoding="utf-8")
    r_nan = run_cli("-i", str(nan_csv), "--validate-only", "--json")
    assert r_nan.returncode == 1
    nan_data = json.loads(r_nan.stdout)
    assert nan_data["usable"] is False
    assert nan_data["nan_values"] == 1
    assert any("non-finite" in e for e in nan_data["errors"])

    # 2. Non-increasing timestamps
    bad_ts_csv = tmp_path / "bad_ts.csv"
    bad_ts_csv.write_text("timestamp,temperature_celsius\n0,4.0\n7200,5.0\n3600,4.5\n", encoding="utf-8")
    r_ts = run_cli("-i", str(bad_ts_csv), "--validate-only")
    assert r_ts.returncode == 1
    assert "INVALID" in r_ts.stdout
    assert "strictly increasing" in r_ts.stdout

    # 3. Fewer than 2 readings
    short_csv = tmp_path / "short.csv"
    short_csv.write_text("timestamp,temperature_celsius\n0,4.0\n", encoding="utf-8")
    r_short = run_cli("validate", "-i", str(short_csv), "--json")
    assert r_short.returncode == 1
    short_data = json.loads(r_short.stdout)
    assert short_data["usable"] is False
    assert short_data["num_readings"] == 1
