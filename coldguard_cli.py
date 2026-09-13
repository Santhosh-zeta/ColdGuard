#!/usr/bin/env python3
"""ColdGuard command-line runner.

Usage:
    python coldguard_cli.py --input data/raw/demo_dpt_power_outage.csv --vaccine DPT
    python coldguard_cli.py --input log.csv --vaccine OPV --initial-potency 0.97
    python coldguard_cli.py --input log.csv --vaccine MMR --output report.json
"""

import argparse
import json
import sys
from pathlib import Path

# Allow running from repo root without installing the package
sys.path.insert(0, str(Path(__file__).parent))

from core.utils import parse_csv_log, run_analysis
from core.decision import Decision


BANNER = {
    Decision.USE:         "\033[92m✅  USE  — Vaccine retains sufficient potency. Safe to administer.\033[0m",
    Decision.INVESTIGATE: "\033[93m⚠️  INVESTIGATE  — Uncertainty high. Consult District Cold Chain Officer.\033[0m",
    Decision.DISCARD:     "\033[91m❌  DISCARD  — Estimated potency below threshold. Do not administer.\033[0m",
}


def main():
    parser = argparse.ArgumentParser(
        description="ColdGuard: Kinetic-Bayesian Vaccine Potency Estimator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--input", "-i", required=True, help="CSV file with timestamp + temperature_celsius columns")
    parser.add_argument("--vaccine", "-v", required=True,
                        choices=["DPT", "OPV", "MMR", "BCG", "HepB", "IPV", "Rotavirus", "PCV"],
                        help="Vaccine type code")
    parser.add_argument("--initial-potency", type=float, default=1.0, metavar="FRAC",
                        help="Initial potency fraction at manufacturing (default 1.0 = 100%%)")
    parser.add_argument("--samples", type=int, default=5000, metavar="N",
                        help="Monte Carlo sample count (default 5000; use 1000 for speed)")
    parser.add_argument("--logger-accuracy", type=float, default=0.5, metavar="DEG_C",
                        help="Logger uncertainty in °C (default 0.5)")
    parser.add_argument("--output", "-o", metavar="FILE",
                        help="Write full JSON result to FILE instead of stdout summary")
    parser.add_argument("--json", action="store_true",
                        help="Print full JSON result to stdout")
    args = parser.parse_args()

    csv_path = Path(args.input)
    if not csv_path.exists():
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        timestamps, temperatures = parse_csv_log(str(csv_path))
    except Exception as exc:
        print(f"Error parsing CSV: {exc}", file=sys.stderr)
        sys.exit(1)

    if len(timestamps) < 2:
        print("Error: temperature log must have at least 2 readings.", file=sys.stderr)
        sys.exit(1)

    result = run_analysis(
        vaccine_type=args.vaccine,
        timestamps=timestamps,
        temperatures_C=temperatures,
        initial_potency=args.initial_potency,
        n_mc_samples=args.samples,
        logger_accuracy_C=args.logger_accuracy,
    )

    dec_out = result["decision_output"]
    post = result["posterior_summary"]

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
            if hasattr(obj, "__dict__"):
                return obj.__dict__
            if hasattr(obj, "value"):  # Enum
                return obj.value
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

    print(BANNER[dec_out.decision])
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
            print(f"    {g['gap_hours']:.1f} h starting {g['gap_start']}")
        print()

    top_segments = sorted(result["segment_attribution"], key=lambda s: s["degradation_fraction"], reverse=True)[:3]
    if top_segments:
        print("  Top degradation segments:")
        for s in top_segments:
            print(f"    {s['duration_hours']:.1f} h at mean {s['mean_temp_C']:.1f}°C  →  {s['degradation_fraction']*100:.1f}% of total loss")
        print()


if __name__ == "__main__":
    main()
