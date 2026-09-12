"""
Vaccine thermostability parameters for Arrhenius kinetic modelling.

All activation energies (Ea) are in J/mol.
A (pre-exponential factor) is in hr^-1.
shelf_life_hours is the nominal shelf life at ref_temp_K.
"""

from dataclasses import dataclass, field
from typing import Dict

R_GAS = 8.314  # J/(mol·K)


@dataclass
class VaccineParams:
    name: str
    Ea_mean: float      # J/mol  – mean activation energy
    Ea_std: float       # J/mol  – standard deviation (parametric uncertainty)
    A: float            # hr^-1  – pre-exponential (Arrhenius) factor
    A_log_std: float    # dimensionless – std of log(A), for log-normal sampling
    shelf_life_hours: float         # hours at ref_temp_K to min_potency_threshold
    ref_temp_K: float               # reference storage temperature (K)
    min_potency_threshold: float    # fraction of initial potency that is acceptable
    freeze_sensitive: bool          # True if freezing damages the vaccine


VACCINE_DB: Dict[str, VaccineParams] = {
    "DPT": VaccineParams(
        name="DPT (Diphtheria-Pertussis-Tetanus)",
        Ea_mean=83_000,
        Ea_std=4_000,
        A=3.37e10,
        A_log_std=0.15,
        shelf_life_hours=17_280,    # 720 days = 2 years
        ref_temp_K=278.15,          # 5°C
        min_potency_threshold=0.80,
        freeze_sensitive=True,
    ),
    "OPV": VaccineParams(
        name="Oral Polio Vaccine",
        Ea_mean=112_000,
        Ea_std=6_000,
        A=5.2e14,
        A_log_std=0.20,
        shelf_life_hours=4_380,     # 182.5 days = 6 months (at −20°C or 2–8°C)
        ref_temp_K=278.15,
        min_potency_threshold=0.67,
        freeze_sensitive=False,
    ),
    "MMR": VaccineParams(
        name="Measles-Mumps-Rubella",
        Ea_mean=108_000,
        Ea_std=7_000,
        A=8.1e15,
        A_log_std=0.22,
        shelf_life_hours=8_760,     # 365 days = 1 year
        ref_temp_K=278.15,
        min_potency_threshold=0.80,
        freeze_sensitive=False,
    ),
    "BCG": VaccineParams(
        name="Bacillus Calmette-Guérin",
        Ea_mean=90_000,
        Ea_std=5_000,
        A=1.2e12,
        A_log_std=0.18,
        shelf_life_hours=8_760,
        ref_temp_K=278.15,
        min_potency_threshold=0.80,
        freeze_sensitive=False,
    ),
    "HepB": VaccineParams(
        name="Hepatitis B",
        Ea_mean=70_000,
        Ea_std=4_500,
        A=2.8e9,
        A_log_std=0.16,
        shelf_life_hours=17_280,
        ref_temp_K=278.15,
        min_potency_threshold=0.80,
        freeze_sensitive=True,
    ),
    "IPV": VaccineParams(
        name="Inactivated Polio Vaccine",
        Ea_mean=92_000,
        Ea_std=5_500,
        A=4.6e12,
        A_log_std=0.19,
        shelf_life_hours=17_280,
        ref_temp_K=278.15,
        min_potency_threshold=0.80,
        freeze_sensitive=True,
    ),
    "Rotavirus": VaccineParams(
        name="Rotavirus Vaccine",
        Ea_mean=100_000,
        Ea_std=6_000,
        A=9.3e13,
        A_log_std=0.21,
        shelf_life_hours=17_520,    # 730 days = 2 years (frozen)
        ref_temp_K=258.15,          # −15°C (frozen reference)
        min_potency_threshold=0.80,
        freeze_sensitive=False,
    ),
    "PCV": VaccineParams(
        name="Pneumococcal Conjugate Vaccine",
        Ea_mean=77_000,
        Ea_std=4_000,
        A=1.5e10,
        A_log_std=0.15,
        shelf_life_hours=17_280,
        ref_temp_K=278.15,
        min_potency_threshold=0.80,
        freeze_sensitive=True,
    ),
}
