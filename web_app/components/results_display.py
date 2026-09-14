"""
Streamlit results display component for ColdGuard.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict

import numpy as np
import streamlit as st
from ..pdf_report import generate_pdf_report

from core.decision import Decision
from .charts import temperature_timeline_chart, potency_distribution_chart
from core.vaccine_params import VACCINE_DB


_DECISION_STYLE = {
    Decision.USE: {
        "color": "#1B5E20",
        "bg": "#E8F5E9",
        "border": "#4CAF50",
        "emoji": "✅",
        "label": "USE",
    },
    Decision.INVESTIGATE: {
        "color": "#E65100",
        "bg": "#FFF3E0",
        "border": "#FF9800",
        "emoji": "⚠️",
        "label": "INVESTIGATE",
    },
    Decision.DISCARD: {
        "color": "#B71C1C",
        "bg": "#FFEBEE",
        "border": "#F44336",
        "emoji": "🚫",
        "label": "DISCARD",
    },
}


def render_results(analysis_result: Dict[str, Any]) -> None:
    """Render the full results panel.

    Parameters
    ----------
    analysis_result : dict
        Output of core.utils.run_analysis.
    """
    decision_out = analysis_result["decision_output"]
    posterior = analysis_result["posterior_summary"]
    params = VACCINE_DB[analysis_result["vaccine_type"]]
    segments = analysis_result["segment_attribution"]
    timestamps = np.array([s["start_ts"] for s in segments] +
                          ([segments[-1]["end_ts"]] if segments else []))
    temperatures = np.array([s["start_temp_C"] for s in segments] +
                             ([segments[-1]["end_temp_C"]] if segments else []))

    # ------------------------------------------------------------------ Banner
    style = _DECISION_STYLE[decision_out.decision]
    st.markdown(
        f"""
        <div style="
            background:{style['bg']};
            border:3px solid {style['border']};
            border-radius:12px;
            padding:24px;
            margin-bottom:20px;
            text-align:center;
        ">
            <div style="font-size:3rem;">{style['emoji']}</div>
            <div style="font-size:2rem;font-weight:700;color:{style['color']};">
                {style['label']}
            </div>
            <div style="font-size:1.1rem;color:{style['color']};margin-top:8px;">
                {decision_out.natural_language_explanation}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------ Potency gauge
    st.subheader("Estimated Potency")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Mean potency",
            f"{decision_out.estimated_potency_pct:.1f}%",
        )
    with col2:
        lo, hi = decision_out.ci_90
        st.metric("90% CI (lower)", f"{lo:.1f}%")
    with col3:
        st.metric("90% CI (upper)", f"{hi:.1f}%")

    st.metric(
        "Confidence (P ≥ threshold)",
        f"{decision_out.confidence * 100:.1f}%",
        help="Probability that true potency is above the minimum acceptable level.",
    )

    # ------------------------------------------------- Potency distribution chart
    if "potency_samples" in analysis_result and analysis_result["potency_samples"] is not None:
        st.plotly_chart(
            potency_distribution_chart(
                analysis_result["potency_samples"],
                posterior,
                params.min_potency_threshold,
            ),
            use_container_width=True,
        )

    # ------------------------------------------------- Temperature timeline chart
    st.subheader("Temperature History")
    if len(timestamps) > 1:
        st.plotly_chart(
            temperature_timeline_chart(timestamps, temperatures, segments),
            use_container_width=True,
        )

    # ------------------------------------------------ Data quality warnings
    warnings = analysis_result.get("data_quality_warnings", [])
    freeze_events = analysis_result.get("freeze_events", [])

    if warnings or freeze_events:
        with st.expander("⚠️ Data Quality Warnings", expanded=True):
            for w in warnings:
                st.warning(w)
            if freeze_events:
                st.error(
                    f"{len(freeze_events)} freeze event(s) detected. "
                    f"This may irreversibly damage freeze-sensitive vaccines."
                )
                if params.freeze_sensitive:
                    st.error(
                        f"{params.name} is freeze-sensitive. "
                        "Please check the shake test and inspect for precipitates."
                    )

    # ----------------------------------------------- Segment attribution
    if segments:
        with st.expander("📊 Segment Degradation Attribution"):
            sorted_segs = sorted(
                segments, key=lambda s: s["degradation_fraction"], reverse=True
            )
            for seg in sorted_segs[:10]:  # top 10
                frac = seg["degradation_fraction"] * 100
                mean_t = seg["mean_temp_C"]
                dur = seg["duration_hours"]
                start_dt = datetime.utcfromtimestamp(seg["start_ts"]).strftime(
                    "%Y-%m-%d %H:%M"
                )
                st.markdown(
                    f"- **{start_dt}** — {mean_t:.1f}°C for {dur:.1f} h → "
                    f"**{frac:.2f}%** of total degradation"
                )

    # ----------------------------------------------- MKT info
    mkt = analysis_result.get("mkt_C")
    if mkt is not None:
        with st.expander("🌡 WHO Mean Kinetic Temperature (MKT)"):
            st.metric("MKT", f"{mkt:.2f}°C")
            st.caption(
                "The MKT is the single temperature that would cause the same "
                "degradation as the actual variable temperature history."
            )

    # ----------------------------------------------- Download report
    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "vaccine_type": analysis_result["vaccine_type"],
        "vaccine_name": analysis_result["vaccine_name"],
        "decision": decision_out.decision.value,
        "confidence": decision_out.confidence,
        "estimated_potency_pct": decision_out.estimated_potency_pct,
        "ci_90": list(decision_out.ci_90),
        "primary_degradation_cause": decision_out.primary_degradation_cause,
        "natural_language_explanation": decision_out.natural_language_explanation,
        "audit_hash": decision_out.audit_hash,
        "posterior_summary": posterior,
        "mkt_C": analysis_result.get("mkt_C"),
        "data_quality_warnings": warnings,
        "freeze_events_count": len(freeze_events),
    }

    st.download_button(
        label="Download JSON report",
        data=json.dumps(report, indent=2),
        file_name=f"coldguard_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        use_container_width=True,
    )

    # -------------------------------------------------- Download PDF report
    pdf_data = generate_pdf_report(report)

    st.download_button(
        label="Download PDF Report",
        data=pdf_data,
        file_name=f"coldguard_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
