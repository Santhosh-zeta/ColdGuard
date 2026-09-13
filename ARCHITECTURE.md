# ColdGuard — Architecture & Developer Reference

## What this is
ColdGuard is a kinetic-Bayesian vaccine potency estimation system for India's
cold chain. Given a temperature log and a vaccine type, it computes remaining
potency with a calibrated 90% confidence interval and outputs a USE/INVESTIGATE/DISCARD
decision with a natural-language explanation.

## Project structure
```
core/           Python scientific engine (Arrhenius, Monte Carlo, decision)
web_app/        Streamlit web application
mobile_app/     React Native / Expo mobile app (Android, offline-first)
simulation/     Synthetic India cold chain scenario generator
validation/     Literature validation and calibration analysis
tests/          pytest test suite (37 tests, all must pass)
notebooks/      Jupyter analysis notebooks (01–05)
data/           raw/ validation/ parameters/ synthetic/
paper/          LaTeX research paper skeleton
docs/           SCIENCE.md  API.md  USER_GUIDE.md
```

## Running the engine

```bash
# Install deps (or use PYTHONPATH=. to skip install)
pip install numpy scipy pandas plotly streamlit pytest

# Run tests
PYTHONPATH=. pytest tests/ -v

# CLI demo
PYTHONPATH=. python coldguard_cli.py \
    --input data/raw/demo_dpt_power_outage.csv \
    --vaccine DPT

# Web app
PYTHONPATH=. streamlit run web_app/app.py
```

## Key design decisions

### Arrhenius integration (core/arrhenius.py)
Temperature must always be in **Kelvin** (`T_celsius + 273.15`). The trapezoidal
rule averages `k(T)` at the endpoints of each interval. Segment attribution sums
to 1.0 via `degradation_fraction`.

### A parameter derivation (core/vaccine_params.py)
All pre-exponential A values were derived from labeled shelf-life using:
```
k_ref = -ln(min_potency) / shelf_life_hours
A = k_ref / exp(-Ea / (R * T_ref_K))
```
Do **not** change A values without re-running the round-trip test in
`tests/test_arrhenius.py::test_a_round_trip`.

### Monte Carlo RNG (core/bayesian.py)
Uses `np.random.default_rng()` (new-style Generator). Tests that need
reproducibility must pass `rng=np.random.default_rng(seed)` explicitly;
`np.random.seed()` does **not** control this RNG.

### Decision thresholds (core/decision.py)
```
P(potency > threshold) > 0.90  →  USE
P(potency > threshold) > 0.70  →  INVESTIGATE
else                           →  DISCARD
```
Thresholds are vaccine-specific: 80% for most; 67% for OPV.

### Mobile engine (mobile_app/src/engine/arrhenius.js)
Full JavaScript port, 1000 Monte Carlo samples for mobile speed. Uses
Box-Muller for Gaussian sampling (no external RNG library). API mirrors
Python core: `runAnalysis(vaccineType, timestamps, temperatures)`.

## Adding a new vaccine
1. Add entry to `VACCINE_DB` in `core/vaccine_params.py` using `VaccineParams`.
2. Derive A from shelf-life using `derive_A_from_shelf_life()`.
3. Add corresponding entry to `VACCINE_DB` in `mobile_app/src/engine/arrhenius.js`.
4. Add at least one scenario CSV to `data/raw/` and a test in `tests/test_scenarios.py`.

## Known limitations / future work
- Ea values are from published ranges, not independently derived from primary stability data.
- Validation data for 5 of 8 vaccines is model-generated (circular); real literature
  data points should be sourced from WHO/GPV/98.07 and manufacturer package inserts.
- Freeze damage is detected but not quantified; a freeze accumulator model is future work.
- Mobile app has not been field-tested on actual Android devices.
- Hindi translations (hi.js) need review by a Hindi-speaking health worker.
