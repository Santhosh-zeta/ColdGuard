"""Smoke tests for the ColdGuard CLI over every bundled scenario."""
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
    import json
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
