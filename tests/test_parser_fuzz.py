"""Bounded fuzzing of logger inputs and API request validation."""
import io
import json
import subprocess
import sys

import numpy as np
import pytest
from fastapi.testclient import TestClient
from hypothesis import given, settings, strategies as st
from pydantic import ValidationError

from api.main import AnalysisRequest, BatchRequest, DHIS2ExportRequest, app
from core.utils import parse_csv_log, parse_json_log

HEADER = "timestamp,temperature_celsius\n"
JSON_VALUES = st.recursive(
    st.none() | st.booleans() | st.integers(-10**1000, 10**1000)
    | st.floats(allow_nan=False, allow_infinity=False) | st.text(max_size=32),
    lambda children: st.lists(children, max_size=4)
    | st.dictionaries(st.text(max_size=12), children, max_size=4),
    max_leaves=12,
)


def assert_log_invariants(result):
    timestamps, temperatures = result
    assert timestamps.ndim == temperatures.ndim == 1
    assert 0 < len(timestamps) == len(temperatures)
    assert np.isfinite(timestamps).all()
    assert np.all(timestamps[1:] > timestamps[:-1])


@settings(max_examples=200, deadline=1000)
@given(blob=st.binary(max_size=2048))
def test_arbitrary_csv_bytes(blob):
    try:
        result = parse_csv_log(io.BytesIO(blob))
    except ValueError:
        return
    assert_log_invariants(result)


@settings(max_examples=200, deadline=1000)
@given(
    timestamps=JSON_VALUES,
    temperatures=JSON_VALUES,
)
def test_arbitrary_json_values(timestamps, temperatures):
    try:
        result = parse_json_log({"timestamps": timestamps, "temperatures_C": temperatures})
    except ValueError:
        return
    assert_log_invariants(result)


@settings(max_examples=100, deadline=1000)
@given(
    readings=st.lists(st.integers(-300, 600), min_size=2, max_size=40),
    separator=st.sampled_from([",", ";", "\t", "|"]),
    encoding=st.sampled_from(["utf-8", "utf-8-sig", "cp1252"]),
)
def test_valid_csv_and_json_round_trip(readings, separator, encoding):
    timestamps = [i * 60 for i in range(len(readings))]
    temperatures = [value / 10 for value in readings]
    header = separator.join(["timestamp", "Température"])
    rows = (f"{ts}{separator}{temp}" for ts, temp in zip(timestamps, temperatures))
    blob = ("\n".join([header, *rows]) + "\n").encode(encoding)
    csv_result = parse_csv_log(io.BytesIO(blob))
    json_result = parse_json_log({"timestamps": timestamps, "temperatures_C": temperatures})
    for result in (csv_result, json_result):
        assert_log_invariants(result)
        np.testing.assert_array_equal(result[0], timestamps)
        np.testing.assert_allclose(result[1], temperatures)


@pytest.mark.parametrize(
    "text",
    [
        "timestamp,timestamp,temperature_celsius\n0,10,5\n1,11,6\n",
        "timestamp,time,temperature_celsius\n0,10,5\n1,11,6\n",
        HEADER + "0,5,9\n1,6,8\n",
        HEADER + "0,5\n1\n",
        HEADER + "0,5\n0,6\n",
        HEADER + "2,5\n1,6\n",
        HEADER + "inf,5\n1,6\n",
        HEADER + '0,5\n1,"unterminated',
        HEADER + "0,5\n1," + "9" * 10000 + "\n",
        HEADER + "0,5\n1,6\x00junk\n",
    ],
)
def test_malformed_csv_is_rejected(text):
    with pytest.raises(ValueError):
        parse_csv_log(io.StringIO(text))


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        {"timestamps": 42, "temperatures_C": [5, 6]},
        {"timestamps": [0, 1], "temperatures_C": [5]},
        {"timestamps": [0, 0], "temperatures_C": [5, 6]},
        {"timestamps": [2, 1], "temperatures_C": [5, 6]},
        {"timestamps": [0, float("nan")], "temperatures_C": [5, 6]},
        {"timestamps": [0, float("inf")], "temperatures_C": [5, 6]},
        {"timestamps": [0, 10**1000], "temperatures_C": [5, 6]},
        {"timestamps": [0, 1], "temperatures_C": [[5], [6]]},
    ],
)
def test_malformed_json_is_rejected(payload):
    with pytest.raises(ValueError):
        parse_json_log(payload)


@settings(max_examples=200, deadline=1000)
@given(timestamps=JSON_VALUES, temperatures=JSON_VALUES)
def test_api_model_handles_arbitrary_json(timestamps, temperatures):
    try:
        request = AnalysisRequest.model_validate(
            {"vaccine": "DPT", "timestamps": timestamps, "temperatures_c": temperatures}
        )
    except ValidationError:
        return
    assert len(request.timestamps) == len(request.temperatures_c) >= 2
    assert all(b > a for a, b in zip(request.timestamps, request.timestamps[1:]))
    assert all(-30 <= t <= 60 for t in request.temperatures_c)


@settings(max_examples=100, deadline=1000)
@given(timestamps=JSON_VALUES, temperatures=JSON_VALUES)
def test_export_model_handles_arbitrary_json(timestamps, temperatures):
    try:
        request = DHIS2ExportRequest.model_validate({
            "vaccine": "DPT", "timestamps": timestamps, "temperatures_c": temperatures,
            "org_unit": "FAC123",
        })
    except ValidationError:
        return
    assert len(request.timestamps) == len(request.temperatures_c) >= 2
    assert all(b > a for a, b in zip(request.timestamps, request.timestamps[1:]))


@settings(max_examples=100, deadline=1000)
@given(batch=JSON_VALUES)
def test_batch_model_handles_arbitrary_json(batch):
    try:
        request = BatchRequest.model_validate({"batch": batch})
    except ValidationError:
        return
    assert 1 <= len(request.batch) <= 100


@pytest.mark.parametrize(
    "body",
    [
        b'{"vaccine":"DPT","timestamps":[',
        json.dumps({"vaccine": "DPT", "timestamps": [0, 0], "temperatures_c": [5, 6]}).encode(),
        json.dumps({"vaccine": "DPT", "timestamps": [0, 1], "temperatures_c": [5]}).encode(),
    ],
)
def test_bad_api_request_returns_4xx(body):
    with TestClient(app) as client:
        response = client.post("/analyse", content=body, headers={"Content-Type": "application/json"})
    assert 400 <= response.status_code < 500


def test_million_row_csv(tmp_path):
    count = 1_000_000
    path = tmp_path / "large.csv"
    with path.open("w", encoding="utf-8", newline="") as output:
        output.write(HEADER)
        for start in range(0, count, 10_000):
            output.writelines(f"{i * 60},5.0\n" for i in range(start, start + 10_000))
    timestamps, temperatures = parse_csv_log(path)
    assert_log_invariants((timestamps, temperatures))
    assert len(timestamps) == count
    assert timestamps[0] == 0 and timestamps[-1] == (count - 1) * 60
    assert np.all(temperatures == 5.0)
    assert timestamps.nbytes + temperatures.nbytes == count * 16
    if sys.platform == "linux":
        # A fresh process avoids counting high-water marks from earlier pytest tests.
        # Keep this intentionally generous: it guards against gross memory regressions,
        # not against modest changes in pandas or the Python allocator.
        script = """
import resource
import sys
from core.utils import parse_csv_log
baseline = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
timestamps, temperatures = parse_csv_log(sys.argv[1])
peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
assert len(timestamps) == len(temperatures) == 1_000_000
assert peak - baseline < 512 * 1024, (baseline, peak)
"""
        subprocess.run([sys.executable, "-c", script, str(path)], check=True, timeout=60)
