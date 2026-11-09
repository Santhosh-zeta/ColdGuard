import numpy as np
import pytest

from core.export import to_dhis2_payload
from core.utils import run_analysis


@pytest.fixture(scope="module")
def result():
    ts = np.arange(0, 24 * 3600, 3600, dtype=float)
    return run_analysis("DPT", ts, np.full(24, 5.0), n_mc_samples=200)


def test_payload_shape(result):
    p = to_dhis2_payload(result, "FAC123", "20260115")
    vals = {v["dataElement"]: v for v in p["dataValues"]}
    assert set(vals) == {"CG_DECISION", "CG_POTENCY_MEAN", "CG_CI90_LOWER",
                         "CG_CI90_UPPER", "CG_VACCINE_TYPE", "CG_AUDIT_HASH"}
    assert all(v["orgUnit"] == "FAC123" and v["period"] == "20260115" for v in vals.values())
    assert vals["CG_VACCINE_TYPE"]["value"] == "DPT"
    assert vals["CG_DECISION"]["value"] in {"USE", "INVESTIGATE", "DISCARD"}


def test_default_period_is_today(result):
    p = to_dhis2_payload(result, "FAC123")
    assert len(p["dataValues"][0]["period"]) == 8


@pytest.mark.parametrize("org,period", [("", "20260115"), ("  ", None), ("F", "2026-01-15")])
def test_invalid_inputs(result, org, period):
    with pytest.raises(ValueError):
        to_dhis2_payload(result, org, period)
