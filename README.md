# ColdGuard 🌡️
**Probabilistic Vaccine Potency Estimation for Cold Chain Management**

> *Stop discarding vaccines that are still potent. Start knowing what you're doing.*

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)

## The Problem

India's Universal Immunisation Programme loses millions of vaccine doses annually to cold chain management failures — not because the vaccines are bad, but because the decision system is broken. A temperature alarm fires; the vaccine is discarded. Even if it was potent. Even if the excursion was brief and harmless.

Simultaneously, undetected or unreported excursions mean degraded vaccines are sometimes administered, reducing immunization efficacy.

## What ColdGuard Does

ColdGuard takes a vaccine vial's temperature log and computes:

- **Estimated remaining potency** (e.g., "DPT: 97.8% potency")
- **90% confidence interval** (e.g., "94–99%")
- **Plain-language recommendation** ("SAFE TO USE / INVESTIGATE / DISCARD")
- **Degradation explanation** ("Primary potency loss: 11 hours at 14°C caused 1.8% loss")

It runs **entirely offline** on a mobile device. It requires **no internet connection**. It was designed for **use by ANMs and cold chain officers** with no statistics background.

## How It Works

1. **Arrhenius kinetics:** Drug degradation follows known kinetic models. At temperature T, degradation rate `k(T) = A·exp(-Ea/RT)`. We integrate this over the full temperature trajectory.

2. **Bayesian uncertainty:** Kinetic parameters and logger readings have known uncertainties. Monte Carlo propagation (5,000 samples) gives calibrated confidence intervals.

3. **Field deployment:** Streamlit web app (offline-capable) + React Native mobile app (English/Hindi).

## Quick Start

```bash
git clone https://github.com/yourusername/coldguard
cd coldguard
pip install -e .
```

### Web Demo

```bash
streamlit run web_app/app.py
```

### Command Line

```bash
python -c "
from core.utils import run_analysis, parse_csv_log
import numpy as np
ts, temps = parse_csv_log('data/raw/brief_excursion_15c.csv')
result = run_analysis('DPT', ts, temps)
print(result['decision'].decision.value, result['posterior']['mean']*100, '%')
"
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 5: FIELD INTERFACE                               │
│  Streamlit Web App  +  React Native Mobile App          │
├─────────────────────────────────────────────────────────┤
│  LAYER 4: DECISION SUPPORT ENGINE (core/decision.py)    │
│  USE / INVESTIGATE / DISCARD  +  natural language       │
├─────────────────────────────────────────────────────────┤
│  LAYER 3: BAYESIAN UNCERTAINTY (core/bayesian.py)       │
│  Monte Carlo · 5,000 samples · posterior distribution   │
├─────────────────────────────────────────────────────────┤
│  LAYER 2: ARRHENIUS ENGINE (core/arrhenius.py)          │
│  Discrete-time integrator · MKT comparison              │
├─────────────────────────────────────────────────────────┤
│  LAYER 1: DATA INPUT (core/utils.py)                    │
│  CSV / JSON / Manual · validation · freeze detection    │
└─────────────────────────────────────────────────────────┘
```

## Supported Vaccines (India UIP)

| Code | Vaccine | Min Potency | Freeze Sensitive |
|------|---------|-------------|------------------|
| DPT | Diphtheria-Pertussis-Tetanus | 80% | Yes |
| OPV | Oral Polio Vaccine | 67% | No |
| MMR | Measles-Mumps-Rubella | 80% | No |
| BCG | Bacillus Calmette-Guérin | 80% | No |
| HepB | Hepatitis B | 80% | Yes |
| IPV | Inactivated Polio Vaccine | 80% | Yes |
| Rotavirus | Rotavirus Vaccine | 80% | No |
| PCV | Pneumococcal Conjugate Vaccine | 80% | Yes |

## Repository Structure

```
coldguard/
├── core/               Scientific engine (Arrhenius + Bayesian + decision)
├── web_app/            Streamlit web application
├── mobile_app/         React Native mobile application
├── simulation/         Protocol comparison simulation study
├── validation/         Validation against published stability data
├── data/               Raw logs, validation datasets, parameters
├── tests/              pytest test suite
├── notebooks/          Jupyter notebooks for analysis
└── docs/               Science, API, and user guide documentation
```

## Running Tests

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Simulation Study

Run the protocol comparison (ColdGuard vs MKT vs VVM):

```bash
python -m simulation.protocol_comparison
```

## Science

Parameters sourced from:
- WHO/IVB/06.10: "Temperature Sensitivity of Vaccines"
- Galazka AM, Milstien J, Zaffran M. "Thermostability of Vaccines." WHO/GPV/98.07
- ICH Q1E: "Evaluation of Stability Data"

See [docs/SCIENCE.md](docs/SCIENCE.md) for the full derivation.

## License

MIT — see [LICENSE](LICENSE).
