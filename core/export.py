"""Export ColdGuard analysis results to external health-information systems."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional


def to_dhis2_payload(
    result: Dict[str, Any],
    org_unit: str,
    period: Optional[str] = None,
) -> Dict[str, Any]:
    """Convert a :func:`core.utils.run_analysis` result into a DHIS2 ``dataValues`` payload.

    Parameters
    ----------
    result : dict
        Output of ``run_analysis``.
    org_unit : str
        DHIS2 organisation-unit UID of the reporting facility.
    period : str, optional
        DHIS2 daily period (``YYYYMMDD``). Defaults to today (UTC).

    Returns
    -------
    dict
        ``{"dataValues": [...]}`` ready to POST to ``/api/dataValueSets``.
        Data-element codes: CG_DECISION, CG_POTENCY_MEAN, CG_CI90_LOWER,
        CG_CI90_UPPER, CG_VACCINE_TYPE, CG_AUDIT_HASH.
    """
    if not org_unit or not org_unit.strip():
        raise ValueError("org_unit is required")
    if period is None:
        period = datetime.now(timezone.utc).strftime("%Y%m%d")
    if len(period) != 8 or not period.isdigit():
        raise ValueError("period must be in YYYYMMDD format")

    dec = result["decision_output"]
    values = {
        "CG_DECISION": dec.decision.value,
        "CG_POTENCY_MEAN": f"{dec.estimated_potency_pct:.1f}",
        "CG_CI90_LOWER": f"{dec.ci_90[0]:.1f}",
        "CG_CI90_UPPER": f"{dec.ci_90[1]:.1f}",
        "CG_VACCINE_TYPE": result["vaccine_type"],
        "CG_AUDIT_HASH": dec.audit_hash,
    }
    return {
        "dataValues": [
            {"dataElement": de, "value": v, "period": period, "orgUnit": org_unit}
            for de, v in values.items()
        ]
    }
