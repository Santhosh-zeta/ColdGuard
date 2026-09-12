"""
ColdGuard Streamlit Web Application.

Run with:
    streamlit run web_app/app.py

The app has three states:
1. INPUT  – form for vaccine type + temperature log
2. PROCESSING – spinner while Monte-Carlo runs
3. RESULTS – full results panel with decision banner, charts, download
"""

from __future__ import annotations

import sys
import os

# Ensure the repository root is on the Python path so that `core` is importable
# whether the app is launched from the project root or the web_app/ directory.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import streamlit as st

# Page config must be the first Streamlit call
st.set_page_config(
    page_title="ColdGuard – Vaccine Potency Estimator",
    page_icon="💉",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from core.utils import run_analysis
from web_app.components.input_form import render_input_form
from web_app.components.results_display import render_results


# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .main-header {
        background: linear-gradient(135deg, #1565C0 0%, #0288D1 100%);
        padding: 2rem 2rem 1rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .main-header h1 { color: white; margin-bottom: 0.25rem; }
    .main-header p  { color: rgba(255,255,255,0.85); font-size: 1.05rem; margin: 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="main-header">
        <h1>💉 ColdGuard</h1>
        <p>
            Kinetic-Bayesian vaccine potency estimation from cold-chain temperature logs.
            Upload a logger CSV or enter readings manually to get an actionable decision.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "state" not in st.session_state:
    st.session_state.state = "input"
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "form_data" not in st.session_state:
    st.session_state.form_data = None

# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------
if st.session_state.state == "input":
    form_data = render_input_form()

    if form_data is not None:
        st.session_state.form_data = form_data
        st.session_state.state = "processing"
        st.rerun()

elif st.session_state.state == "processing":
    form_data = st.session_state.form_data

    with st.spinner("Running Bayesian analysis … this may take a few seconds."):
        import numpy as np

        try:
            result = run_analysis(
                vaccine_type=form_data["vaccine_type"],
                timestamps=form_data["timestamps"],
                temperatures_C=form_data["temperatures_C"],
                initial_potency=form_data.get("initial_potency", 1.0),
                n_mc_samples=form_data.get("n_mc_samples", 2000),
            )
            st.session_state.analysis_result = result
            st.session_state.state = "results"
            st.rerun()
        except Exception as e:
            st.error(f"Analysis failed: {e}")
            st.session_state.state = "input"

elif st.session_state.state == "results":
    result = st.session_state.analysis_result

    if result is None:
        st.session_state.state = "input"
        st.rerun()

    render_results(result)

    st.markdown("---")
    if st.button("← Analyse another vaccine", use_container_width=True):
        st.session_state.state = "input"
        st.session_state.analysis_result = None
        st.session_state.form_data = None
        st.rerun()
