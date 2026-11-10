"""
I/O utilities and the top-level pipeline runner for ColdGuard.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import IO, Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from dateutil import parser as dtparser

from .arrhenius import (
    compute_potency,
    compute_segment_attribution,
    compute_mkt,
    mkt_potency_estimate,
    compute_freeze_damage_fraction,
)
from .bayesian import monte_carlo_potency_distribution, compute_posterior_summary
from .decision import make_decision
from .vaccine_params import FREEZE_THRESHOLD_C, VACCINE_DB


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

_CANDIDATE_DELIMITERS = (",", ";", "\t", "|")


def _read_text(source: Union[str, Path, IO]) -> Tuple[str, str]:
    """Return ``(text, label)`` for a path or an open file-like object.

    Decodes UTF-8 (a leading BOM is dropped); falls back to cp1252, which
    spreadsheet exports from Windows tools often use.
    """
    if hasattr(source, "read"):
        raw = source.read()
        label = "<input>"
    else:
        raw = Path(source).read_bytes()
        label = str(source)
    if isinstance(raw, bytes):
        try:
            raw = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            raw = raw.decode("cp1252", errors="replace")
    elif raw.startswith("\ufeff"):
        raw = raw[1:]
    return raw, label


def _detect_delimiter(text: str) -> str:
    """Pick the delimiter from the header line (names never contain decimals).

    Using the header avoids the classic trap of a ``;``-separated file with
    decimal commas, where commas also occur in every data row.
    """
    header = next((ln for ln in text.splitlines() if ln.strip()), "")
    counts = {d: header.count(d) for d in _CANDIDATE_DELIMITERS}
    best = max(_CANDIDATE_DELIMITERS, key=lambda d: counts[d])
    return best if counts[best] > 0 else ","


def parse_csv_log(filepath: Union[str, Path, IO]) -> Tuple[np.ndarray, np.ndarray]:
    """Parse a temperature log CSV (a path or an open text/binary file object).

    Expected columns: ``timestamp`` (ISO-8601 or Unix) and a temperature column
    (``temperature_celsius``, or any column name containing ``temp``).

    Handles the common export variants automatically:

    - delimiter: comma, semicolon, tab or pipe (detected from the header line)
    - decimal separator: dot or comma (``5,2``)
    - UTF-8 byte-order mark, and Windows (cp1252) encoding

    Returns
    -------
    timestamps : np.ndarray
        Unix timestamps in seconds (float64).
    temperatures_C : np.ndarray
        Temperature readings in °C (float64).

    Raises
    ------
    ValueError
        If the file cannot be parsed. Messages name the columns that were found
        or the offending row, so the user can fix the file.
    """
    text, label = _read_text(filepath)
    delimiter = _detect_delimiter(text)
    try:
        df = pd.read_csv(io.StringIO(text), sep=delimiter, skipinitialspace=True)
    except (pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise ValueError(f"Failed to parse CSV file {label}: {exc}") from exc

    # Normalise column names
    col_map = {}
    for col in df.columns:
        low = str(col).strip().lower().replace(" ", "_").replace("-", "_")
        if low in ("timestamp", "ts", "time", "datetime"):
            col_map[col] = "timestamp"
        elif "temp" in low or low in ("t_c", "tc"):
            col_map[col] = "temperature_celsius"
    df = df.rename(columns=col_map)

    found = [str(c) for c in df.columns]
    if "timestamp" not in df.columns:
        raise ValueError(f"Cannot find timestamp column in {label}. Found columns: {found}")
    if "temperature_celsius" not in df.columns:
        raise ValueError(f"Cannot find temperature column in {label}. Found columns: {found}")

    # Convert timestamps
    ts_raw = df["timestamp"]
    if pd.api.types.is_numeric_dtype(ts_raw):
        timestamps = ts_raw.values.astype(float)
    else:
        timestamps = np.array(
            [dtparser.parse(str(t)).timestamp() for t in ts_raw], dtype=float
        )

    # Temperatures: numbers as-is; text columns may use a decimal comma ("5,2").
    temp_raw = df["temperature_celsius"]
    if pd.api.types.is_numeric_dtype(temp_raw):
        temperatures_C = temp_raw.values.astype(float)
    else:
        cleaned = temp_raw.astype(str).str.strip().str.replace(",", ".", regex=False)
        cleaned = cleaned.where(temp_raw.notna() & (cleaned != ""), other=None)
        numeric = pd.to_numeric(cleaned, errors="coerce")
        bad = numeric.isna() & cleaned.notna()
        if bad.any():
            row = int(np.flatnonzero(bad.values)[0])
            raise ValueError(
                f"Temperature value {temp_raw.iloc[row]!r} in row {row + 1} of {label} "
                "is not a number"
            )
        temperatures_C = numeric.values.astype(float)
    return timestamps, temperatures_C


def parse_json_log(data_dict: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
    """Parse a temperature log from a dict (e.g. loaded from JSON).

    Expects keys ``timestamps`` (list of ISO-8601 strings or unix ints)
    and ``temperatures_C`` (list of floats).

    Returns
    -------
    timestamps : np.ndarray  (Unix seconds)
    temperatures_C : np.ndarray  (°C)
    """
    raw_ts = data_dict.get("timestamps", data_dict.get("timestamp", []))
    raw_tc = data_dict.get("temperatures_C", data_dict.get("temperature_celsius", []))

    if not raw_ts or not raw_tc:
        raise ValueError("data_dict must have 'timestamps' and 'temperatures_C' keys")

    if isinstance(raw_ts[0], (int, float)):
        timestamps = np.asarray(raw_ts, dtype=float)
    else:
        timestamps = np.array(
            [dtparser.parse(str(t)).timestamp() for t in raw_ts], dtype=float
        )

    temperatures_C = np.asarray(raw_tc, dtype=float)
    return timestamps, temperatures_C


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_temperature_log(
    timestamps: np.ndarray, temperatures: np.ndarray
) -> List[str]:
    """Return a list of warning strings for potential data quality issues.

    Checks performed:
    - At least 2 data points
    - Timestamps are strictly increasing
    - Temperatures within physically plausible range (−30 to 60 °C)
    - Logging gaps > 4 hours
    """
    warnings: List[str] = []
    ts = np.asarray(timestamps, dtype=float)
    tc = np.asarray(temperatures, dtype=float)

    if len(ts) < 2:
        warnings.append("Temperature log has fewer than 2 data points.")
        return warnings

    if np.any(np.diff(ts) <= 0):
        warnings.append("Timestamps are not strictly increasing.")

    if np.any(tc < -30) or np.any(tc > 60):
        warnings.append(
            f"Temperature readings outside expected range −30 to 60 °C "
            f"(min={tc.min():.1f}, max={tc.max():.1f})."
        )

    gaps = detect_logging_gaps(ts, max_gap_hours=4.0)
    for gap in gaps:
        warnings.append(
            f"Logging gap of {gap['duration_hours']:.1f} h detected between "
            f"readings at index {gap['index_before']} and {gap['index_after']}."
        )

    return warnings


def detect_freeze_events(
    temperatures_C: np.ndarray, threshold: float = FREEZE_THRESHOLD_C
) -> List[Dict[str, Any]]:
    """Identify contiguous segments where temperature falls below *threshold*.

    Parameters
    ----------
    temperatures_C : array-like
    threshold : float
        Temperature (°C) below which a freeze event is declared. Default ``FREEZE_THRESHOLD_C`` (0°C).

    Returns
    -------
    list of dict
        Each dict has keys: start_index, end_index, min_temp_C, duration_readings.
    """
    tc = np.asarray(temperatures_C, dtype=float)
    below = tc < threshold
    events: List[Dict[str, Any]] = []

    i = 0
    while i < len(below):
        if below[i]:
            j = i
            while j < len(below) and below[j]:
                j += 1
            events.append(
                {
                    "start_index": i,
                    "end_index": j - 1,
                    "min_temp_C": float(np.min(tc[i:j])),
                    "duration_readings": j - i,
                }
            )
            i = j
        else:
            i += 1
    return events


def detect_logging_gaps(
    timestamps: np.ndarray, max_gap_hours: float = 4.0
) -> List[Dict[str, Any]]:
    """Identify intervals larger than *max_gap_hours* in the timestamp series.

    Returns
    -------
    list of dict
        Keys: index_before, index_after, duration_hours.
    """
    ts = np.asarray(timestamps, dtype=float)
    gaps: List[Dict[str, Any]] = []
    diffs_h = np.diff(ts) / 3600.0
    for idx, dh in enumerate(diffs_h):
        if dh > max_gap_hours:
            gaps.append(
                {
                    "index_before": idx,
                    "index_after": idx + 1,
                    "duration_hours": float(dh),
                }
            )
    return gaps


# ---------------------------------------------------------------------------
# Full pipeline runner
# ---------------------------------------------------------------------------

def run_analysis(
    vaccine_type: str,
    timestamps: np.ndarray,
    temperatures_C: np.ndarray,
    initial_potency: float = 1.0,
    n_mc_samples: int = 5_000,
    logger_accuracy_C: float = 0.5,
    rng: Optional[np.random.Generator] = None,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """Run the complete ColdGuard analysis pipeline.

    Parameters
    ----------
    vaccine_type : str
        Key into VACCINE_DB, e.g. "DPT".
    timestamps : array-like
        Unix timestamps in seconds.
    temperatures_C : array-like
        Temperature readings in °C.
    initial_potency : float
        Starting potency fraction (default 1.0 = 100%).
    n_mc_samples : int
        Monte-Carlo sample count.
    logger_accuracy_C : float
        Data-logger 1-sigma accuracy in °C.
    rng : np.random.Generator, optional
        Seeded generator for reproducibility.
    seed : int, optional
        Convenience alternative to *rng*; the same seed gives identical output.

    Raises
    ------
    ValueError
        If the vaccine is unknown, fewer than 2 readings are given, lengths
        differ, readings contain NaN/inf, or timestamps are not strictly
        increasing.

    Returns
    -------
    dict with keys:
        vaccine_type, vaccine_name,
        data_quality_warnings,
        freeze_events,
        logging_gaps,
        point_estimate_potency,
        mkt_C,
        mkt_potency_estimate,
        segment_attribution,
        posterior_summary,
        decision_output (DecisionOutput),
        potency_samples (np.ndarray)
    """
    if vaccine_type not in VACCINE_DB:
        raise ValueError(
            f"Unknown vaccine type '{vaccine_type}'. "
            f"Available: {list(VACCINE_DB.keys())}"
        )

    params = VACCINE_DB[vaccine_type]
    ts = np.asarray(timestamps, dtype=float)
    tc = np.asarray(temperatures_C, dtype=float)

    if len(ts) != len(tc):
        raise ValueError("timestamps and temperatures_C must have the same length")
    if len(ts) < 2:
        raise ValueError("At least 2 temperature readings are required")
    for name, values in (("timestamps", ts), ("temperatures_C", tc)):
        non_finite = np.flatnonzero(~np.isfinite(values))
        if non_finite.size:
            raise ValueError(
                f"Temperature log contains non-finite values at index "
                f"{int(non_finite[0])} in {name}"
            )
    if np.any(np.diff(ts) <= 0):
        raise ValueError(
            "Timestamps must be strictly increasing (found out-of-order or duplicate timestamps)"
        )
    if rng is None and seed is not None:
        rng = np.random.default_rng(seed)

    # Data quality
    warnings = validate_temperature_log(ts, tc)
    freeze_events = detect_freeze_events(tc)
    logging_gaps = detect_logging_gaps(ts)

    # Point estimates
    thermal_potency = compute_potency(ts, tc, params.Ea_mean, params.A, initial_potency)
    freeze_retention = compute_freeze_damage_fraction(ts, tc, params)
    point_potency = thermal_potency * freeze_retention
    mkt_C = compute_mkt(tc, Ea=params.Ea_mean, timestamps=ts)
    mkt_pot = mkt_potency_estimate(ts, tc, params)
    segments = compute_segment_attribution(ts, tc, params.Ea_mean, params.A)

    # Bayesian inference
    samples = monte_carlo_potency_distribution(
        ts,
        tc,
        params,
        n_samples=n_mc_samples,
        initial_potency=initial_potency,
        logger_accuracy_C=logger_accuracy_C,
        rng=rng,
    )
    posterior = compute_posterior_summary(
        samples, threshold=params.min_potency_threshold
    )

    # Decision
    decision_out = make_decision(
        posterior,
        params,
        segments,
        freeze_events=freeze_events,
        freeze_damage_retention=freeze_retention,
    )

    return {
        "vaccine_type": vaccine_type,
        "vaccine_name": params.name,
        "data_quality_warnings": warnings,
        "freeze_events": freeze_events,
        "logging_gaps": logging_gaps,
        "point_estimate_potency": point_potency,
        "freeze_damage_retention": freeze_retention,
        "mkt_C": mkt_C,
        "mkt_potency_estimate": mkt_pot,
        "segment_attribution": segments,
        "posterior_summary": posterior,
        "decision_output": decision_out,
        "potency_samples": samples,
        "seed": seed,
    }
