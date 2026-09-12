"""
Synthetic cold-chain temperature profile generator.

Uses statistical profiles (power outages, excursions, freeze events) to
produce realistic temperature histories for simulation studies.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple

import numpy as np


@dataclass
class ColdChainProfile:
    """Parameterised cold-chain profile for synthetic scenario generation."""

    name: str
    base_temp_C: float = 4.0
    base_temp_std_C: float = 0.5

    # Warm excursions
    excursion_freq_per_day: float = 0.1          # mean events per day
    excursion_duration_hours_mean: float = 3.0
    excursion_duration_hours_std: float = 1.5
    excursion_temp_mean_C: float = 15.0
    excursion_temp_std_C: float = 4.0

    # Freeze events
    freeze_freq_per_day: float = 0.02
    freeze_duration_hours_mean: float = 1.0
    freeze_duration_hours_std: float = 0.5

    # Power outages
    power_outage_freq_per_day: float = 0.1
    power_outage_duration_hours_mean: float = 2.0
    power_outage_temp_rise_C_per_hour: float = 1.5

    # Data-logger gaps
    logging_gap_freq_per_day: float = 0.05
    logging_gap_hours_mean: float = 5.0

    resolution_minutes: int = 60


# Built-in India profiles
INDIA_DISTRICT = ColdChainProfile(
    name="india_district",
    base_temp_C=4.5,
    base_temp_std_C=0.8,
    excursion_freq_per_day=0.15,
    excursion_duration_hours_mean=3.5,
    excursion_duration_hours_std=1.5,
    excursion_temp_mean_C=14.0,
    excursion_temp_std_C=4.0,
    freeze_freq_per_day=0.05,
    freeze_duration_hours_mean=1.0,
    freeze_duration_hours_std=0.5,
    power_outage_freq_per_day=0.2,
    power_outage_duration_hours_mean=2.0,
    power_outage_temp_rise_C_per_hour=1.5,
    logging_gap_freq_per_day=0.03,
    logging_gap_hours_mean=5.0,
)

INDIA_PHC = ColdChainProfile(
    name="india_phc",
    base_temp_C=5.0,
    base_temp_std_C=1.2,
    excursion_freq_per_day=0.25,
    excursion_duration_hours_mean=4.0,
    excursion_duration_hours_std=2.0,
    excursion_temp_mean_C=16.0,
    excursion_temp_std_C=5.0,
    freeze_freq_per_day=0.08,
    freeze_duration_hours_mean=1.5,
    freeze_duration_hours_std=0.8,
    power_outage_freq_per_day=0.35,
    power_outage_duration_hours_mean=3.5,
    power_outage_temp_rise_C_per_hour=2.0,
    logging_gap_freq_per_day=0.10,
    logging_gap_hours_mean=8.0,
)

INDIA_OUTREACH = ColdChainProfile(
    name="india_outreach",
    base_temp_C=6.0,
    base_temp_std_C=2.0,
    excursion_freq_per_day=0.60,
    excursion_duration_hours_mean=2.0,
    excursion_duration_hours_std=1.0,
    excursion_temp_mean_C=28.0,
    excursion_temp_std_C=6.0,
    freeze_freq_per_day=0.15,
    freeze_duration_hours_mean=0.5,
    freeze_duration_hours_std=0.25,
    power_outage_freq_per_day=0.0,
    power_outage_duration_hours_mean=0.0,
    power_outage_temp_rise_C_per_hour=0.0,
    logging_gap_freq_per_day=0.40,
    logging_gap_hours_mean=6.0,
)


def generate_scenario(
    profile: ColdChainProfile,
    total_duration_days: float = 7.0,
    rng: Optional[np.random.Generator] = None,
    resolution_minutes: int = 60,
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate a synthetic temperature history.

    Parameters
    ----------
    profile : ColdChainProfile
    total_duration_days : float
    rng : np.random.Generator, optional
    resolution_minutes : int
        Time between readings in minutes.

    Returns
    -------
    timestamps : np.ndarray
        Unix-like relative timestamps in seconds (starting at 0).
    temperatures : np.ndarray
        Temperature readings in °C.
    """
    if rng is None:
        rng = np.random.default_rng()

    step_s = resolution_minutes * 60
    total_s = int(total_duration_days * 86_400)
    n_steps = total_s // step_s + 1
    timestamps = np.arange(n_steps, dtype=float) * step_s

    # Start with base temperatures
    temps = rng.normal(profile.base_temp_C, profile.base_temp_std_C, n_steps)

    step_hours = resolution_minutes / 60.0
    total_hours = total_duration_days * 24.0

    # Helper: mark contiguous segments
    def _apply_event(start_h, duration_h, peak_temp_C, shape="flat"):
        start_idx = int(start_h / step_hours)
        end_idx = min(int((start_h + duration_h) / step_hours), n_steps)
        for idx in range(start_idx, end_idx):
            if shape == "flat":
                t = peak_temp_C + rng.normal(0, 0.3)
            else:  # ramp up then ramp down
                mid = (start_idx + end_idx) / 2
                frac = 1.0 - abs(idx - mid) / ((end_idx - start_idx) / 2 + 1e-9)
                t = profile.base_temp_C + (peak_temp_C - profile.base_temp_C) * frac
                t += rng.normal(0, 0.4)
            temps[idx] = t

    # Warm excursions
    n_excursions = rng.poisson(profile.excursion_freq_per_day * total_duration_days)
    for _ in range(n_excursions):
        start_h = rng.uniform(0, total_hours)
        dur_h = max(
            0.5,
            rng.normal(
                profile.excursion_duration_hours_mean,
                profile.excursion_duration_hours_std,
            ),
        )
        exc_temp = rng.normal(profile.excursion_temp_mean_C, profile.excursion_temp_std_C)
        exc_temp = max(exc_temp, profile.base_temp_C + 5)
        _apply_event(start_h, dur_h, exc_temp, shape="ramp")

    # Freeze events
    n_freezes = rng.poisson(profile.freeze_freq_per_day * total_duration_days)
    for _ in range(n_freezes):
        start_h = rng.uniform(0, total_hours)
        dur_h = max(
            0.25,
            rng.normal(
                profile.freeze_duration_hours_mean,
                profile.freeze_duration_hours_std,
            ),
        )
        freeze_temp = rng.normal(-3.0, 2.0)
        freeze_temp = min(freeze_temp, -0.5)
        _apply_event(start_h, dur_h, freeze_temp, shape="flat")

    # Power outages (temperature rises gradually)
    if profile.power_outage_freq_per_day > 0:
        n_outages = rng.poisson(
            profile.power_outage_freq_per_day * total_duration_days
        )
        for _ in range(n_outages):
            start_h = rng.uniform(0, total_hours)
            dur_h = max(
                0.5,
                rng.exponential(profile.power_outage_duration_hours_mean),
            )
            peak_temp = profile.base_temp_C + dur_h * profile.power_outage_temp_rise_C_per_hour
            _apply_event(start_h, dur_h, peak_temp, shape="ramp")

    return timestamps, temps
