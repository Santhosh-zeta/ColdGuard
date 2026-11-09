"""Regression tests for safety-critical correctness fixes."""
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from api.main import app
from core import __version__
from core.arrhenius import compute_freeze_damage_fraction, compute_mkt, integrate_degradation
from core.bayesian import monte_carlo_potency_distribution
from core.utils import detect_freeze_events, run_analysis
from core.vaccine_params import FREEZE_THRESHOLD_C, R_GAS, VACCINE_DB

ROOT = Path(__file__).parent.parent
HOURLY = np.arange(0, 24 * 3600, 3600, dtype=float)


# --- timestamps ------------------------------------------------------------

@pytest.mark.parametrize("bad", [
    [0, 3600, 3600, 7200],      # duplicate
    [0, 7200, 3600, 10800],     # out of order
])
def test_run_analysis_rejects_non_increasing_timestamps(bad):
    with pytest.raises(ValueError, match="strictly increasing"):
        run_analysis("DPT", np.array(bad, float), np.full(4, 5.0), n_mc_samples=100)


def test_run_analysis_rejects_short_or_mismatched_logs():
    with pytest.raises(ValueError):
        run_analysis("DPT", np.array([0.0]), np.array([5.0]), n_mc_samples=100)
    with pytest.raises(ValueError):
        run_analysis("DPT", np.array([0.0, 1.0]), np.array([5.0]), n_mc_samples=100)


def test_api_returns_422_for_unsorted_timestamps():
    r = TestClient(app).post("/analyse", json={
        "vaccine": "DPT", "timestamps": [3600, 0, 7200], "temperatures_c": [5, 5, 5]})
    assert r.status_code == 422


# --- time-weighted MKT -----------------------------------------------------

def test_mkt_is_time_weighted():
    ea = 83_000
    # 1 hot reading, then 100 cold readings packed into 1 hour: the hot period
    # lasts ~23 h, so a time-weighted MKT must be much hotter than a plain mean.
    ts = np.concatenate([[0.0], 82_800 + np.arange(100) * 36.0])
    tc = np.concatenate([[25.0], np.full(100, 5.0)])
    unweighted = compute_mkt(tc, Ea=ea)
    weighted = compute_mkt(tc, Ea=ea, timestamps=ts)
    assert weighted > unweighted + 5


def test_mkt_constant_temperature():
    tc = np.full(24, 6.0)
    assert compute_mkt(tc, Ea=83_000, timestamps=HOURLY) == pytest.approx(6.0, abs=1e-6)
    assert compute_mkt(tc, Ea=83_000) == pytest.approx(6.0, abs=1e-6)


# --- seed / reproducibility ------------------------------------------------

def test_same_seed_same_result():
    tc = 4 + np.sin(np.arange(24))
    a = run_analysis("DPT", HOURLY, tc, n_mc_samples=500, seed=7)
    b = run_analysis("DPT", HOURLY, tc, n_mc_samples=500, seed=7)
    c = run_analysis("DPT", HOURLY, tc, n_mc_samples=500, seed=8)
    assert a["decision_output"].audit_hash == b["decision_output"].audit_hash
    assert a["seed"] == 7
    assert np.array_equal(a["potency_samples"], b["potency_samples"])
    assert not np.array_equal(a["potency_samples"], c["potency_samples"])


def test_api_seed_reproducible():
    client = TestClient(app)
    body = {"vaccine": "DPT", "timestamps": list(range(0, 36000, 3600)),
            "temperatures_c": [5.0] * 10, "n_mc_samples": 200, "seed": 3}
    r1, r2 = client.post("/analyse", json=body).json(), client.post("/analyse", json=body).json()
    assert r1["decision_output"]["audit_hash"] == r2["decision_output"]["audit_hash"]
    assert r1["seed"] == 3


def test_cli_seed_reproducible():
    def run():
        return subprocess.run(
            [sys.executable, "coldguard_cli.py", "-i", "data/raw/normal_cold_storage.csv",
             "-v", "DPT", "--samples", "300", "--seed", "1", "--json"],
            capture_output=True, text=True, cwd=ROOT, env={"PYTHONPATH": str(ROOT), "PATH": ""})
    a, b = run(), run()
    assert a.returncode == 0, a.stderr
    assert a.stdout == b.stdout


# --- vectorised Monte Carlo matches the reference implementation -----------

def test_vectorised_mc_matches_reference_loop():
    params = VACCINE_DB["DPT"]
    tc = 8 + 4 * np.sin(np.arange(24) / 3)
    n = 4000
    fast = monte_carlo_potency_distribution(HOURLY, tc, params, n_samples=n,
                                            rng=np.random.default_rng(0))
    # Reference: original per-sample loop, same RNG draw order.
    rng = np.random.default_rng(0)
    Ea = rng.normal(params.Ea_mean, params.Ea_std, size=n)
    A = np.exp(rng.normal(math.log(params.A), params.A_log_std, size=n))
    noise = rng.normal(0.0, 0.5, size=(n, len(tc)))
    ref = np.array([
        math.exp(-integrate_degradation(HOURLY, tc + noise[i], Ea[i], A[i]))
        for i in range(n)
    ]) * compute_freeze_damage_fraction(HOURLY, tc, params)
    np.testing.assert_allclose(fast, np.clip(ref, 0, 1), rtol=1e-9, atol=1e-12)


# --- freeze threshold ------------------------------------------------------

def test_freeze_threshold_is_unified():
    assert FREEZE_THRESHOLD_C == 0.0
    tc = np.array([5.0, -0.5, -0.5, 5.0])
    assert len(detect_freeze_events(tc)) == 1
    ts = np.array([0.0, 3600.0, 7200.0, 10800.0])
    assert compute_freeze_damage_fraction(ts, tc, VACCINE_DB["DPT"]) < 1.0


# --- version ---------------------------------------------------------------

def test_api_version_matches_package():
    client = TestClient(app)
    assert client.get("/health").json()["version"] == __version__
    assert client.get("/").json()["version"] == __version__
    assert app.version == __version__
    assert R_GAS > 0
