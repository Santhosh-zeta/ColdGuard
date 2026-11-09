#!/usr/bin/env python3
"""ColdGuard command-line runner.

Usage:
    python coldguard_cli.py --input data/raw/demo_dpt_power_outage.csv --vaccine DPT
    python coldguard_cli.py --input log.csv --vaccine OPV --initial-potency 0.97
    python coldguard_cli.py --input log.csv --vaccine MMR --output report.json
    python coldguard_cli.py --input log.csv --validate-only
"""

import argparse
import json
import os
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Dict

# Allow running from repo root without installing the package
sys.path.insert(0, str(Path(__file__).parent))

from core import __version__
from core.utils import (
    detect_freeze_events,
    detect_logging_gaps,
    parse_csv_log,
    run_analysis,
    validate_temperature_log,
)
from core.decision import Decision
from core.vaccine_params import VACCINE_DB


BANNER_TEXT = {
    Decision.USE:         "✅  USE  — Vaccine retains sufficient potency. Safe to administer.",
    Decision.INVESTIGATE: "⚠️  INVESTIGATE  — Uncertainty high. Consult District Cold Chain Officer.",
    Decision.DISCARD:     "❌  DISCARD  — Estimated potency below threshold. Do not administer.",
}

BANNER_COLOR = {
    Decision.USE:         "\033[92m",
    Decision.INVESTIGATE: "\033[93m",
    Decision.DISCARD:     "\033[91m",
}

BANNER = {
    decision: f"{BANNER_COLOR[decision]}{text}\033[0m"
    for decision, text in BANNER_TEXT.items()
}


def should_use_color(no_color: bool = False) -> bool:
    if no_color or os.environ.get("NO_COLOR", "") != "":
        return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def format_banner(decision: Decision, *, use_color: bool = True) -> str:
    return BANNER[decision] if use_color else BANNER_TEXT[decision]


def validate_log(timestamps: Any, temperatures: Any) -> Dict[str, Any]:
    import numpy as np

    ts = np.asarray(timestamps, dtype=float)
    tc = np.asarray(temperatures, dtype=float)

    num_readings = int(len(ts))
    ts_finite = np.isfinite(ts)
    tc_finite = np.isfinite(tc)
    nan_ts_indices = [int(i) for i in np.flatnonzero(~ts_finite)]
    nan_tc_indices = [int(i) for i in np.flatnonzero(~tc_finite)]
    nan_values = len(nan_ts_indices) + len(nan_tc_indices)

    diffs = np.diff(ts) if len(ts) >= 2 else np.array([], dtype=float)
    non_increasing_mask = np.isfinite(diffs) & (diffs <= 0)
    non_increasing_timestamps = int(np.sum(non_increasing_mask))

    finite_ts = ts[ts_finite]
    if len(finite_ts) >= 2:
        time_span_hours = float((finite_ts[-1] - finite_ts[0]) / 3600.0)
    else:
        time_span_hours = 0.0

    pos_diffs = diffs[np.isfinite(diffs) & (diffs > 0)]
    finite_diffs = diffs[np.isfinite(diffs)]
    if len(pos_diffs) > 0:
        sampling_interval_seconds = float(np.median(pos_diffs))
        sampling_interval_minutes = float(sampling_interval_seconds / 60.0)
    elif len(finite_diffs) > 0:
        sampling_interval_seconds = float(np.median(finite_diffs))
        sampling_interval_minutes = float(sampling_interval_seconds / 60.0)
    else:
        sampling_interval_seconds = None
        sampling_interval_minutes = None

    finite_tc = tc[tc_finite]
    if len(finite_tc) > 0:
        min_temp_C = float(np.min(finite_tc))
        max_temp_C = float(np.max(finite_tc))
    else:
        min_temp_C = None
        max_temp_C = None

    warnings = validate_temperature_log(ts, tc)
    logging_gaps = detect_logging_gaps(ts) if len(ts) >= 2 else []
    freeze_events = detect_freeze_events(tc)
    freeze_readings = int(sum(e["duration_readings"] for e in freeze_events))

    errors = []
    if len(ts) != len(tc):
        errors.append("timestamps and temperatures_C must have the same length.")
    if len(ts) < 2:
        errors.append("Temperature log must have at least 2 readings.")
    if nan_ts_indices:
        errors.append(
            f"Temperature log contains non-finite values at index {nan_ts_indices[0]} in timestamps."
        )
    if nan_tc_indices:
        errors.append(
            f"Temperature log contains non-finite values at index {nan_tc_indices[0]} in temperatures_C."
        )
    if non_increasing_timestamps > 0:
        errors.append(
            "Timestamps must be strictly increasing (found out-of-order or duplicate timestamps)."
        )

    return {
        "usable": len(errors) == 0,
        "num_readings": num_readings,
        "time_span_hours": time_span_hours,
        "sampling_interval_seconds": sampling_interval_seconds,
        "sampling_interval_minutes": sampling_interval_minutes,
        "min_temp_C": min_temp_C,
        "max_temp_C": max_temp_C,
        "logging_gaps": logging_gaps,
        "freeze_events": freeze_events,
        "freeze_readings": freeze_readings,
        "non_increasing_timestamps": non_increasing_timestamps,
        "nan_values": nan_values,
        "data_quality_warnings": warnings,
        "errors": errors,
    }


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="ColdGuard: Kinetic-Bayesian Vaccine Potency Estimator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--version", action="version", version=f"coldguard {__version__}")
    parser.add_argument("--input", "-i", required=True, help="CSV file with timestamp + temperature_celsius columns")
    parser.add_argument("--vaccine", "-v", required=False,
                        choices=sorted(VACCINE_DB),
                        help="Vaccine type code (required unless --validate-only is used)")
    parser.add_argument("--initial-potency", type=float, default=1.0, metavar="FRAC",
                        help="Initial potency fraction at manufacturing (default 1.0 = 100%%)")
    parser.add_argument("--samples", type=int, default=5000, metavar="N",
                        help="Monte Carlo sample count (default 5000; use 1000 for speed)")
    parser.add_argument("--logger-accuracy", type=float, default=0.5, metavar="DEG_C",
                        help="Logger uncertainty in °C (default 0.5)")
    parser.add_argument("--seed", type=int, default=None, metavar="N",
                        help="RNG seed for reproducible results")
    parser.add_argument("--output", "-o", metavar="FILE",
                        help="Write full JSON result to FILE instead of stdout summary")
    parser.add_argument("--json", action="store_true",
                        help="Print full JSON result to stdout")
    parser.add_argument("--no-color", action="store_true",
                        help="Disable ANSI colour codes in output")
    parser.add_argument("--validate-only", "--validate", dest="validate_only", action="store_true",
                        help="Validate the input CSV and report data-quality findings without running the analysis")

    argv = sys.argv[1:]
    if argv and argv[0] == "validate":
        argv = ["--validate-only", *argv[1:]]
    args = parser.parse_args(argv)

    if not args.validate_only and not args.vaccine:
        parser.error("the following arguments are required: --vaccine/-v")

    csv_path = Path(args.input)
    if not csv_path.exists():
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        timestamps, temperatures = parse_csv_log(str(csv_path))
    except Exception as exc:
        if args.validate_only and (args.json or args.output):
            err_report = {
                "usable": False,
                "num_readings": 0,
                "time_span_hours": 0.0,
                "sampling_interval_seconds": None,
                "sampling_interval_minutes": None,
                "min_temp_C": None,
                "max_temp_C": None,
                "logging_gaps": [],
                "freeze_events": [],
                "freeze_readings": 0,
                "non_increasing_timestamps": 0,
                "nan_values": 0,
                "data_quality_warnings": [],
                "errors": [str(exc)],
            }
            json_text = json.dumps(err_report, indent=2)
            if args.output:
                Path(args.output).write_text(json_text, encoding="utf-8")
                print(f"JSON report written to {args.output}")
            else:
                print(json_text)
        print(f"Error parsing CSV: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.validate_only:
        report = validate_log(timestamps, temperatures)
        if args.json or args.output:
            json_text = json.dumps(report, indent=2)
            if args.output:
                Path(args.output).write_text(json_text, encoding="utf-8")
                print(f"JSON report written to {args.output}")
            else:
                print(json_text)
            sys.exit(0 if report["usable"] else 1)

        print()
        print(f"ColdGuard Log Validation — {args.input}")
        print("=" * 60)

        use_color = should_use_color(args.no_color)
        if report["usable"]:
            status_line = "✅  VALID  — Log is usable for ColdGuard potency analysis."
            if use_color:
                status_line = f"\033[92m{status_line}\033[0m"
        else:
            status_line = "❌  INVALID  — Log cannot be analysed."
            if use_color:
                status_line = f"\033[91m{status_line}\033[0m"
        print(status_line)
        print()

        if report["sampling_interval_minutes"] is not None:
            interval_str = f"{report['sampling_interval_minutes']:.1f} min ({report['sampling_interval_seconds']:.0f} s)"
        else:
            interval_str = "N/A"

        if report["min_temp_C"] is not None and report["max_temp_C"] is not None:
            temp_range_str = f"{report['min_temp_C']:.1f}°C to {report['max_temp_C']:.1f}°C"
        else:
            temp_range_str = "N/A"

        print(f"  Readings                 : {report['num_readings']}")
        print(f"  Time span                : {report['time_span_hours']:.1f} h")
        print(f"  Sampling interval        : {interval_str}")
        print(f"  Min / max temperature    : {temp_range_str}")
        print(f"  Logging gaps (>4 h)      : {len(report['logging_gaps'])}")
        print(f"  Freeze readings (<0°C)   : {report['freeze_readings']} ({len(report['freeze_events'])} events)")
        print(f"  Non-increasing timestamps: {report['non_increasing_timestamps']}")
        print(f"  NaN / non-finite values  : {report['nan_values']}")
        print()

        if report["errors"]:
            print("Errors:")
            for err in report["errors"]:
                print(f"  ✖  {err}")
            print()

        if report["data_quality_warnings"]:
            print("Warnings:")
            for w in report["data_quality_warnings"]:
                print(f"  ⚠  {w}")
            print()

        sys.exit(0 if report["usable"] else 1)

    if len(timestamps) < 2:
        print("Error: temperature log must have at least 2 readings.", file=sys.stderr)
        sys.exit(1)

    try:
        result = run_analysis(
            vaccine_type=args.vaccine,
            timestamps=timestamps,
            temperatures_C=temperatures,
            initial_potency=args.initial_potency,
            n_mc_samples=args.samples,
            logger_accuracy_C=args.logger_accuracy,
            seed=args.seed,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    dec_out = result["decision_output"]

    if args.json or args.output:
        # Serialize the result (convert non-JSON-native types)
        def _serialize(obj):
            import numpy as np
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, Enum):
                return obj.value
            if hasattr(obj, "__dict__"):
                return obj.__dict__
            return str(obj)

        out_dict = {k: v for k, v in result.items() if k != "potency_samples"}
        json_text = json.dumps(out_dict, default=_serialize, indent=2)

        if args.output:
            Path(args.output).write_text(json_text)
            print(f"JSON report written to {args.output}")
        else:
            print(json_text)
        return

    # Human-readable summary
    print()
    print(f"ColdGuard Analysis — {result['vaccine_name']}")
    print("=" * 60)

    if result["data_quality_warnings"]:
        print("Warnings:")
        for w in result["data_quality_warnings"]:
            print(f"  ⚠  {w}")
        print()

    if result["freeze_events"]:
        print("  🧊 FREEZE WARNING: freeze events detected.")
        print()

    print(format_banner(dec_out.decision, use_color=should_use_color(args.no_color)))
    print()
    print(f"  Potency estimate : {dec_out.estimated_potency_pct:.1f}%")
    print(f"  90% CI           : {dec_out.ci_90[0]:.1f}% – {dec_out.ci_90[1]:.1f}%")
    print(f"  Confidence       : {dec_out.confidence*100:.0f}%")
    print()
    print(f"  {dec_out.natural_language_explanation}")
    print()
    print(f"  MKT: {result['mkt_C']:.2f}°C   Point estimate: {result['point_estimate_potency']*100:.2f}%")
    print(f"  Audit hash: {dec_out.audit_hash[:16]}…")
    print()

    if result["logging_gaps"]:
        print("  Logging gaps (unmonitored periods):")
        for g in result["logging_gaps"]:
            print(f"    {g['duration_hours']:.1f} h after reading #{g['index_before']}")
        print()

    top_segments = sorted(result["segment_attribution"], key=lambda s: s["degradation_fraction"], reverse=True)[:3]
    if top_segments:
        print("  Top degradation segments:")
        for s in top_segments:
            print(f"    {s['duration_hours']:.1f} h at mean {s['mean_temp_C']:.1f}°C  →  {s['degradation_fraction']*100:.1f}% of total loss")
        print()


if __name__ == "__main__":
    main()
