"""
Streamlit input form component for ColdGuard.
"""

from __future__ import annotations

import io
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
import streamlit as st

from core.vaccine_params import VACCINE_DB


def render_input_form() -> Optional[Dict[str, Any]]:
    """Render the ColdGuard input form and return collected data on submission.

    Returns
    -------
    dict or None
        dict with keys: vaccine_type, timestamps (unix array),
        temperatures_C (array), initial_potency, n_mc_samples
        Returns None if the user has not yet submitted.
    """
    st.subheader("Vaccine & Temperature Data Entry")

    col1, col2 = st.columns(2)

    with col1:
        vaccine_type = st.selectbox(
            "Vaccine type",
            options=list(VACCINE_DB.keys()),
            format_func=lambda k: f"{k} – {VACCINE_DB[k].name}",
        )

    with col2:
        initial_potency = st.slider(
            "Initial potency (% at manufacture)",
            min_value=80, max_value=100, value=100, step=1,
        ) / 100.0

    n_mc_samples = st.select_slider(
        "Monte-Carlo samples (more = more precise, slower)",
        options=[500, 1000, 2000, 5000, 10000],
        value=2000,
    )

    st.markdown("---")
    input_mode = st.radio(
        "Temperature log input",
        options=["Upload CSV file", "Enter readings manually"],
        horizontal=True,
    )

    timestamps = None
    temperatures_C = None

    if input_mode == "Upload CSV file":
        uploaded = st.file_uploader(
            "Upload temperature log CSV (columns: timestamp, temperature_celsius)",
            type=["csv"],
        )
        if uploaded is not None:
            try:
                df = pd.read_csv(uploaded)
                # Normalize columns
                col_map = {}
                for col in df.columns:
                    low = col.lower().replace(" ", "_").replace("-", "_")
                    if low in ("timestamp", "ts", "time", "datetime"):
                        col_map[col] = "timestamp"
                    elif "temp" in low:
                        col_map[col] = "temperature_celsius"
                df = df.rename(columns=col_map)

                if "timestamp" not in df.columns or "temperature_celsius" not in df.columns:
                    st.error("CSV must have 'timestamp' and 'temperature_celsius' columns.")
                else:
                    from dateutil import parser as dtparser
                    ts_raw = df["timestamp"]
                    if pd.api.types.is_numeric_dtype(ts_raw):
                        timestamps = ts_raw.values.astype(float)
                    else:
                        timestamps = np.array(
                            [dtparser.parse(str(t)).timestamp() for t in ts_raw],
                            dtype=float,
                        )
                    temperatures_C = df["temperature_celsius"].values.astype(float)
                    st.success(f"Loaded {len(timestamps)} readings.")
                    st.dataframe(df.head(10), use_container_width=True)
            except Exception as e:
                st.error(f"Error reading CSV: {e}")

    else:  # Manual entry
        st.caption("Add temperature readings below (at least 2 required).")
        start_date = st.date_input("Start date", value=datetime.today().date())
        start_time = st.time_input("Start time", value=datetime.now().replace(
            minute=0, second=0, microsecond=0).time())
        interval_h = st.number_input(
            "Interval between readings (hours)", min_value=0.25, value=1.0, step=0.25
        )

        n_readings = st.number_input(
            "Number of readings to enter", min_value=2, max_value=200, value=10
        )

        default_temps = [4.0] * int(n_readings)
        rows = []
        for i in range(int(n_readings)):
            dt = datetime.combine(start_date, start_time) + timedelta(hours=interval_h * i)
            label = dt.strftime("%Y-%m-%d %H:%M")
            temp = st.number_input(
                f"T at {label} (°C)", value=4.0, step=0.1, key=f"temp_{i}",
                min_value=-30.0, max_value=60.0,
            )
            rows.append({"timestamp": dt.timestamp(), "temperature_celsius": temp})

        if rows:
            timestamps = np.array([r["timestamp"] for r in rows], dtype=float)
            temperatures_C = np.array([r["temperature_celsius"] for r in rows], dtype=float)

    st.markdown("---")
    submitted = st.button("Analyse vaccine potency", type="primary", use_container_width=True)

    if submitted:
        if timestamps is None or temperatures_C is None:
            st.error("Please provide temperature data before analysing.")
            return None
        if len(timestamps) < 2:
            st.error("At least 2 temperature readings are required.")
            return None

        return {
            "vaccine_type": vaccine_type,
            "timestamps": timestamps,
            "temperatures_C": temperatures_C,
            "initial_potency": initial_potency,
            "n_mc_samples": n_mc_samples,
        }

    return None
