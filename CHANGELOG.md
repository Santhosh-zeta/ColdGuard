# Changelog

All notable changes to ColdGuard are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Added
- `seed` option on `run_analysis`, the CLI (`--seed`) and the API for reproducible results; the seed is echoed in responses
- `POST /batch-analyse` (many CSV logs per request) and `POST /export/dhis2`; `core/export.py` (`to_dhis2_payload`)
- Dockerfile, docker-compose.yml, `.dockerignore`
- Complete Tamil and Bengali translations; automated i18n key-parity test
- `CITATION.cff`, `.editorconfig`, translation issue template, REST API docs

### Fixed
- Readings that are NaN or infinite are rejected with a clear error (HTTP 422 on both `/analyse` and `/export/dhis2`) instead of reporting a NaN potency
- Out-of-order or duplicate timestamps are now rejected (`ValueError` / HTTP 422) instead of producing negative degradation
- MKT is now time-weighted when timestamps are supplied
- Freeze-event detection and freeze-damage accounting now share one threshold (0 °C, `FREEZE_THRESHOLD_C`)
- Decision uses P(potency ≥ the vaccine's own threshold) instead of the 0.80/0.67 buckets
- CLI: crash on logging gaps, only 8 of 12 vaccines accepted, and `--json` serialising the `Decision` enum as a raw class dict
- Mobile: duplicate/mismatched dependency versions; added missing `@react-native-picker/picker` and `babel-preset-expo`; aligned to Expo SDK 57
- API version now comes from package metadata; pydantic v2 idioms; correct posterior-mean potency
- Build: invalid `build-backend`, conflicting `setup.py` removed; CI now installs API/PDF dependencies and runs the mobile tests

### Changed
- Installation is now modular: the core install no longer pulls in Streamlit, Plotly, Matplotlib, ReportLab or FastAPI; use the `web`, `api`, `dev` and `research` extras (`pip install -e ".[web,api,dev]"`). `requirements.txt` now just installs `-e .[web,api,dev]`. Thanks @nanjundachitra100-del (#103)
- Monte Carlo is vectorised (about 7× faster)
- CI: Python 3.11/3.12 matrix, concurrency control, mobile Jest job

- Freeze damage accumulator: first-order freeze kinetics in `core/arrhenius.py`, applied to all freeze-sensitive vaccines (DPT, HepB, IPV, PCV, Typhoid, MenA)
- QR code scanner in the mobile app for Berlinger Fridge-tag logger IDs (camera-based)
- VACCINE_DB expanded from 8 to 12 UIP vaccines: added Yellow Fever (YF), Japanese Encephalitis (JE), Typhoid Vi-PS, and Meningitis A (MenA)

### Planned
- Real literature-sourced validation data for BCG, HepB, IPV, Rotavirus, PCV
- PyMC full Bayesian MCMC posterior as alternative to Monte Carlo
- eVIN API integration for national cold chain reporting

---

## [0.1.0] — 2026-09-13

### Added

**Scientific Engine (`core/`)**
- `arrhenius.py` — Arrhenius degradation integrator using trapezoidal rule; `k(T) = A·exp(-Ea/RT)`. Includes segment attribution (fraction of total degradation per time interval), WHO Mean Kinetic Temperature (MKT) computation, and `derive_A_from_shelf_life()` utility.
- `bayesian.py` — Monte Carlo uncertainty propagation (5,000 samples by default). Samples `Ea ~ Normal(μ, σ)`, `ln(A) ~ Normal(ln(A_mean), σ_lnA)`, and sensor noise `ε ~ Normal(0, 0.5°C)`. Returns full posterior summary with 90%/95% credible intervals.
- `decision.py` — Decision engine mapping `P(potency > threshold)` to USE/INVESTIGATE/DISCARD with natural-language explanation and SHA-256 audit hash.
- `vaccine_params.py` — `VaccineParams` dataclass and `VACCINE_DB` with all 8 India UIP vaccines (DPT, OPV, MMR, BCG, HepB, IPV, Rotavirus, PCV). All A values correctly derived from labeled shelf-life specifications using the round-trip formula.
- `utils.py` — `run_analysis()` top-level pipeline; CSV/JSON parsing; freeze event and logging gap detection; input validation.

**Web Application**
- Streamlit 3-state UI: input form → processing → results
- Color-coded USE/INVESTIGATE/DISCARD decision banner
- Plotly temperature timeline with excursion highlighting
- Monte Carlo potency distribution chart with 90% CI band
- Segment attribution breakdown expander
- PDF audit report download

**Mobile Application**
- React Native + Expo offline-first Android app
- Full JavaScript port of the scientific engine (`arrhenius.js`) with 1,000-sample Monte Carlo
- Box-Muller Gaussian sampling (no external RNG library)
- English / Hindi language toggle via `LangContext`
- Screens: InputScreen, ProcessingScreen, ResultsScreen
- Components: DecisionBanner, PotencyChart, TemperatureTimeline

**CLI**
- `coldguard_cli.py` — Command-line runner with `--input`, `--vaccine`, `--initial-potency`, `--samples`, `--logger-accuracy`, `--output`, `--json` flags
- Color-coded terminal output with potency estimate, CI, segment attribution

**Test Suite**
- 37 tests across 4 modules: `test_arrhenius.py` (8), `test_bayesian.py` (7), `test_decision.py` (8), `test_scenarios.py` (14)
- All 10 synthetic cold chain scenarios tested end-to-end

**Data**
- 10 synthetic temperature CSV scenarios: normal cold storage, brief/extended excursion, multiple excursions, near-freeze, logging gap, transport, outreach, freeze event, worst-case
- Demo scenario: `data/raw/demo_dpt_power_outage.csv` (DPT, 11h at 14.3°C)
- Validation datasets for DPT, OPV, and Measles (MMR)
- `data/parameters/vaccine_arrhenius_db.json`

**Simulation**
- `simulation/cold_chain_generator.py` — `ColdChainProfile` dataclass; District, PHC, and Outreach scenario profiles
- `simulation/protocol_comparison.py` — ColdGuard vs MKT vs VVM, FDR/FUR metrics, McNemar's test

**Validation**
- `validation/literature_validation.py` — round-trip validation against published stability data
- `validation/calibration_analysis.py` — coverage probability, RMSE, MAE, Bland-Altman

**Notebooks**
- `01_arrhenius_exploration.ipynb` — Arrhenius rate curves for all 8 vaccines
- `02_parameter_derivation.ipynb` — A value derivation from shelf-life
- `03_validation_analysis.ipynb` — Scenario-level validation analysis
- `04_simulation_study.ipynb` — 1,000-scenario ColdGuard vs MKT vs VVM comparison
- `05_paper_figures.ipynb` — Generates all publication-ready figures

**Research Paper Skeleton**
- `paper/main.tex` — Full 7-section LaTeX paper with equations, parameter tables, figure placeholders
- `paper/references.bib` — WHO/GPV/98.07, WHO/IVB/06.10, ICH Q1E, Matthias et al.

**Documentation**
- `docs/SCIENCE.md` — Arrhenius derivation, Bayesian uncertainty propagation, decision logic, vaccine parameter table with primary sources
- `docs/API.md` — Complete public API reference for `core/`
- `docs/USER_GUIDE.md` — Step-by-step guide for ANMs and cold chain officers

**CI/CD & Open Source**
- `.github/workflows/test.yml` — GitHub Actions CI: 37 tests + CLI smoke test on every push/PR
- `.github/dependabot.yml` — Automated dependency security updates
- Issue templates: bug report, feature request, vaccine addition
- Pull request template
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`
- `ARCHITECTURE.md` — Repository context: design decisions, invariants, dev setup

### Initial Contributors
- [Santhosh-zeta](https://github.com/Santhosh-zeta) — Project creator and lead developer

---

[Unreleased]: https://github.com/Santhosh-zeta/ColdGuard/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Santhosh-zeta/ColdGuard/releases/tag/v0.1.0
