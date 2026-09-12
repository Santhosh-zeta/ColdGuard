"""
Plotly chart components for ColdGuard web application.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def temperature_timeline_chart(
    timestamps: np.ndarray,
    temperatures: np.ndarray,
    segment_attribution: List[Dict[str, Any]],
) -> go.Figure:
    """Temperature history chart with excursions highlighted.

    Parameters
    ----------
    timestamps : np.ndarray
        Unix timestamps (seconds).
    temperatures : np.ndarray
        Temperature readings in °C.
    segment_attribution : list of dict
        Segment breakdown from core.arrhenius.compute_segment_attribution.

    Returns
    -------
    go.Figure
    """
    from datetime import datetime

    dt_labels = [
        datetime.utcfromtimestamp(float(t)).strftime("%Y-%m-%d %H:%M") for t in timestamps
    ]
    temps = np.asarray(temperatures, dtype=float)

    fig = go.Figure()

    # Main temperature trace
    fig.add_trace(
        go.Scatter(
            x=dt_labels,
            y=temps,
            mode="lines+markers",
            line=dict(color="#2196F3", width=2),
            marker=dict(size=4),
            name="Temperature (°C)",
        )
    )

    # Shade excursion segments (>8°C) in orange
    # Shade freeze segments (<0°C) in blue
    for seg in segment_attribution:
        mean_t = seg["mean_temp_C"]
        if mean_t > 8.0:
            fill_color = "rgba(255,152,0,0.25)"  # orange
        elif mean_t < 0.0:
            fill_color = "rgba(33,150,243,0.3)"   # blue
        else:
            continue

        ts_start = float(seg["start_ts"])
        ts_end = float(seg["end_ts"])
        dt_start = datetime.utcfromtimestamp(ts_start).strftime("%Y-%m-%d %H:%M")
        dt_end = datetime.utcfromtimestamp(ts_end).strftime("%Y-%m-%d %H:%M")

        fig.add_vrect(
            x0=dt_start,
            x1=dt_end,
            fillcolor=fill_color,
            layer="below",
            line_width=0,
        )

    # Reference lines
    fig.add_hline(y=8.0, line_dash="dash", line_color="orange",
                  annotation_text="8°C threshold", annotation_position="bottom right")
    fig.add_hline(y=0.0, line_dash="dot", line_color="steelblue",
                  annotation_text="Freeze risk", annotation_position="top right")

    fig.update_layout(
        title="Temperature History",
        xaxis_title="Date / Time (UTC)",
        yaxis_title="Temperature (°C)",
        hovermode="x unified",
        template="plotly_white",
        height=350,
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig


def potency_distribution_chart(
    potency_samples: np.ndarray,
    posterior_summary: Dict[str, float],
    threshold: float,
) -> go.Figure:
    """Histogram of the MC potency posterior with CI bands.

    Parameters
    ----------
    potency_samples : np.ndarray
    posterior_summary : dict
    threshold : float
        Minimum acceptable potency fraction.

    Returns
    -------
    go.Figure
    """
    pct_samples = potency_samples * 100
    mean_pct = posterior_summary["mean"] * 100
    ci_lo = posterior_summary["ci_90_lower"] * 100
    ci_hi = posterior_summary["ci_90_upper"] * 100
    thresh_pct = threshold * 100

    fig = go.Figure()

    fig.add_trace(
        go.Histogram(
            x=pct_samples,
            nbinsx=60,
            marker_color="#42A5F5",
            opacity=0.75,
            name="MC samples",
        )
    )

    # Mean line
    fig.add_vline(x=mean_pct, line_color="darkblue", line_width=2,
                  annotation_text=f"Mean {mean_pct:.1f}%",
                  annotation_position="top right")

    # CI band
    fig.add_vrect(
        x0=ci_lo, x1=ci_hi,
        fillcolor="rgba(66,165,245,0.15)",
        line_color="rgba(66,165,245,0.5)",
        annotation_text="90% CI",
        annotation_position="top left",
    )

    # Threshold line
    fig.add_vline(x=thresh_pct, line_dash="dash", line_color="red", line_width=2,
                  annotation_text=f"Min {thresh_pct:.0f}%",
                  annotation_position="bottom left")

    fig.update_layout(
        title="Potency Distribution (Monte-Carlo posterior)",
        xaxis_title="Estimated Potency (%)",
        yaxis_title="Count",
        template="plotly_white",
        height=300,
        margin=dict(l=40, r=20, t=50, b=40),
        showlegend=False,
    )
    return fig
