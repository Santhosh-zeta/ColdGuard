<div align="center">

# 🧊 ColdGuard

### Kinetic-Bayesian Vaccine Potency Estimation for India's Cold Chain

*Don't discard vaccines that are still potent. Don't administer ones that aren't.*

[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-3b82f6.svg)](https://python.org)
[![CI](https://github.com/Santhosh-zeta/ColdGuard/actions/workflows/test.yml/badge.svg)](https://github.com/Santhosh-zeta/ColdGuard/actions/workflows/test.yml)
[![Lint](https://github.com/Santhosh-zeta/ColdGuard/actions/workflows/lint.yml/badge.svg)](https://github.com/Santhosh-zeta/ColdGuard/actions/workflows/lint.yml)
[![Platform](https://img.shields.io/badge/Platform-Web%20%7C%20Android%20%7C%20CLI-8b5cf6.svg)]()
[![Offline](https://img.shields.io/badge/Works-Offline-f59e0b.svg)]()
[![Languages](https://img.shields.io/badge/Language-EN%20%7C%20हिन्दी%20%7C%20தமிழ்%20%7C%20বাংলা%20%7C%20తెలుగు%20%7C%20ಕನ್ನಡ-ef4444.svg)](mobile_app/src/i18n/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

<br/>

> **ColdGuard** is a science-grade, field-deployable decision support tool for ANMs, cold chain officers, and PHC staff. Given a temperature log, it tells you — with calibrated confidence — whether a vaccine is still safe to use.

</div>

---

## The Problem

India's Universal Immunisation Programme delivers **390 million doses per year** through a cold chain network that stretches from national vaccine stores to village-level outreach sessions. Temperature excursions happen at every tier — power cuts, broken ice packs, transport delays.

Current protocols respond with one of two equally bad choices:

| Protocol | Problem |
|----------|---------|
| **Discard on any alarm** | Destroys potent vaccines. Millions of doses wasted every year. Costs money, erodes trust. |
| **Use it anyway** | Risks administering under-potent doses. Children aren't protected. |
| **VVM (Vaccine Vial Monitor)** | Binary indicator, conservatively calibrated. High false discard rate. No confidence interval. |

**ColdGuard replaces guesswork with physics.**

---

## What's New

- 🔁 **Reproducible results** — `--seed` (CLI) / `seed` (API, Python) gives byte-identical output
- 🛡️ **Safer on bad input** — out-of-order or duplicate timestamps are rejected (API returns 422) instead of silently inflating potency
- ⏱️ **Time-weighted MKT** — irregular logging intervals no longer bias Mean Kinetic Temperature
- ❄️ **One freeze threshold** (0 °C) for both freeze-event detection and freeze-damage accounting
- ⚡ **Vectorised Monte Carlo** — about 7× faster at 5,000 samples × 1,000 readings
- 🎯 **Exact per-vaccine thresholds** — the decision uses P(potency ≥ that vaccine's threshold)
- 🔌 **Integrations** — batch REST endpoint, DHIS2 export, Docker
- 🌐 **Complete Tamil & Bengali** translations, with an automated key-parity test across all 6 languages

See [CHANGELOG.md](CHANGELOG.md) for details.

---

## How It Works

```mermaid
flowchart TD
    A([📂 Temperature Log\nCSV · JSON · Manual]) --> B[Input Validation\nFreeze Detection · Gap Detection]
    B --> C[Arrhenius Integration\nk·T = A·exp−Ea÷RT\nTrapezoidal Rule]
    C --> D[Monte Carlo Sampling\n5000 iterations\nEa · A · Sensor Noise]
    D --> E[Posterior Distribution\n90% Credible Interval\nP·potency > threshold]
    E --> F{Decision Engine}
    F -->|P > 90%| G([🟢 USE\nSafe to administer])
    F -->|70% < P ≤ 90%| H([🟡 INVESTIGATE\nContact district officer])
    F -->|P ≤ 70%| I([🔴 DISCARD\nDo not administer])
    E --> J[Natural Language\nExplanation]
    E --> K[SHA-256 Audit Hash\nSegment Attribution]
```

---

## The Science in One Equation

Vaccine degradation follows **first-order Arrhenius kinetics**. For a discrete temperature log:

$$P_{\text{remaining}} = \exp\!\left(-\sum_{i} \frac{k(T_i) + k(T_{i+1})}{2} \cdot \Delta t_i\right) \qquad k(T) = A \cdot e^{-E_a / RT}$$

ColdGuard propagates uncertainty in **Eₐ**, **A**, and **sensor readings** through 5,000 Monte Carlo samples to produce a calibrated posterior, not just a point estimate.

---

## System Architecture

```mermaid
graph TB
    subgraph INTERFACES["🖥️ Field Interfaces"]
        WEB["Streamlit Web App\n(Offline-capable)"]
        MOB["React Native Mobile\n(Android · Offline)"]
        CLI["Command-Line Runner\ncoldguard_cli.py"]
    end

    subgraph CORE["⚙️ Scientific Engine (core/)"]
        UTILS["utils.py\nParsing · Validation\nFreeze & Gap Detection"]
        ARR["arrhenius.py\nDegradation Integration\nMKT · Segment Attribution"]
        BAYES["bayesian.py\nMonte Carlo · 5000 samples\nPosterior Summary"]
        DEC["decision.py\nUSE · INVESTIGATE · DISCARD\nAudit Hash · NL Explanation"]
        PARAMS["vaccine_params.py\n12 Vaccines\nDerived A values"]
    end

    subgraph DATA["📊 Data & Research"]
        RAW["data/raw/\n10 Scenario CSVs"]
        SIM["simulation/\nCold Chain Generator\nProtocol Comparison"]
        VAL["validation/\nLiterature Validation\nCalibration Analysis"]
        NB["notebooks/\n5 Jupyter Notebooks"]
        PAPER["paper/\nLaTeX Research Paper"]
    end

    INTERFACES --> CORE
    CORE --> DATA
    UTILS --> ARR --> BAYES --> DEC
    PARAMS --> ARR
```

---

## Quick Start

### Web App

```bash
git clone https://github.com/Santhosh-zeta/ColdGuard.git
cd ColdGuard
pip install -e ".[web]"

PYTHONPATH=. streamlit run web_app/app.py
```

### Command Line

```bash
# Demo: DPT vaccine after an 11-hour power outage
PYTHONPATH=. python coldguard_cli.py \
    --input data/raw/demo_dpt_power_outage.csv \
    --vaccine DPT

# Output JSON report
PYTHONPATH=. python coldguard_cli.py \
    --input data/raw/extended_excursion_25c.csv \
    --vaccine OPV \
    --output report.json
```

### Python API

```python
from core.utils import parse_csv_log, run_analysis

timestamps, temperatures = parse_csv_log("data/raw/demo_dpt_power_outage.csv")

result = run_analysis(
    vaccine_type="DPT",
    timestamps=timestamps,
    temperatures_C=temperatures,
    n_mc_samples=5000,
)

dec = result["decision_output"]
print(dec.decision.value)              # "USE"
print(dec.estimated_potency_pct)       # 99.8
print(dec.ci_90)                       # (99.2, 100.0)
print(dec.natural_language_explanation)
```

### REST API & Docker

```bash
# Local
pip install -e ".[api]"
uvicorn api.main:app --reload          # docs at http://localhost:8000/docs

# Docker (CLI + API, no local Python needed)
docker compose up api
docker compose run --rm cli -i data/raw/demo_dpt_power_outage.csv -v DPT --seed 42
```

| Endpoint | Purpose |
|----------|---------|
| `POST /analyse` | Analyse one temperature log (optional `seed` for reproducible output) |
| `POST /batch-analyse` | Analyse many CSV logs in one request, with per-item error handling |
| `POST /export/dhis2` | Analyse and return a DHIS2 `dataValues` payload |
| `GET /vaccines`, `GET /health` | Metadata |

Full reference: [docs/API.md](docs/API.md).

### Run Tests

```bash
pip install -e ".[web,api,dev]"
PYTHONPATH=. python -m pytest tests/ -v
# 107 passed ✅
```

---

## Integrations

- **DHIS2** — `POST /export/dhis2` (or `core.export.to_dhis2_payload`) emits a `dataValues` payload for national health-information dashboards. See [docs/API.md](docs/API.md).
- **REST batch audits** — `POST /batch-analyse` analyses many CSV logs in one call.
- **Docker** — `docker compose up api` serves the REST API on port 8000.

## Supported Vaccines — India UIP

```mermaid
graph LR
    subgraph FREEZE["🧊 Freeze-Sensitive"]
        DPT["DPT\nEa = 83 kJ/mol\nMin: 80%"]
        HEPB["Hep B\nEa = 70 kJ/mol\nMin: 80%"]
        IPV["IPV\nEa = 92 kJ/mol\nMin: 80%"]
        PCV["PCV\nEa = 77 kJ/mol\nMin: 80%"]
        TYP["Typhoid Vi-PS\nEa = 80 kJ/mol\nMin: 80%"]
        MENA["MenA\nEa = 85 kJ/mol\nMin: 80%"]
    end
    subgraph HEAT["🌡️ Heat-Sensitive"]
        OPV["OPV\nEa = 112 kJ/mol\nMin: 67%"]
        MMR["MMR\nEa = 108 kJ/mol\nMin: 80%"]
        BCG["BCG\nEa = 90 kJ/mol\nMin: 80%"]
        ROTA["Rotavirus\nEa = 100 kJ/mol\nMin: 80%"]
        YF["Yellow Fever\nEa = 110 kJ/mol\nMin: 80%"]
        JE["Jap. Encephalitis\nEa = 95 kJ/mol\nMin: 80%"]
    end
```

| Code | Vaccine | Eₐ (kJ/mol) | Shelf Life | Ref Temp | Min Potency | Freeze Sensitive |
|------|---------|:-----------:|:----------:|:--------:|:-----------:|:----------------:|
| DPT | Diphtheria-Pertussis-Tetanus | 83 ± 4 | 24 months | 5°C | 80% | ⚠️ Yes |
| OPV | Oral Polio Vaccine | 112 ± 6 | 6 months | 5°C | 67% | ✅ No |
| MMR | Measles-Mumps-Rubella | 108 ± 7 | 12 months | 5°C | 80% | ✅ No |
| BCG | Bacillus Calmette-Guérin | 90 ± 5 | 12 months | 5°C | 80% | ✅ No |
| HepB | Hepatitis B | 70 ± 4.5 | 24 months | 5°C | 80% | ⚠️ Yes |
| IPV | Inactivated Polio Vaccine | 92 ± 5.5 | 24 months | 5°C | 80% | ⚠️ Yes |
| Rotavirus | Rotavirus Vaccine | 100 ± 6 | 24 months | −15°C | 80% | ✅ No |
| PCV | Pneumococcal Conjugate Vaccine | 77 ± 4 | 24 months | 5°C | 80% | ⚠️ Yes |
| YF | Yellow Fever Vaccine | 110 ± 7 | 24 months | 5°C | 80% | ✅ No |
| JE | Japanese Encephalitis Vaccine | 95 ± 5.5 | 24 months | 5°C | 80% | ✅ No |
| Typhoid | Typhoid Vi Polysaccharide Vaccine | 80 ± 4.5 | 24 months | 5°C | 80% | ⚠️ Yes |
| MenA | Meningitis A Conjugate Vaccine | 85 ± 5 | 24 months | 5°C | 80% | ⚠️ Yes |

---

## Decision Logic

```mermaid
flowchart LR
    A["Monte Carlo\n5000 samples"] --> B["Compute\nP potency > Pmin"]
    B --> C{Probability}
    C -->|"> 90%"| D["🟢 USE\nHigh confidence\nvaccine is potent"]
    C -->|"70% – 90%"| E["🟡 INVESTIGATE\nUncertainty too high\ncall district officer"]
    C -->|"< 70%"| F["🔴 DISCARD\nLikely below\npotency threshold"]
```

---

## Cold Chain Tiers — India Simulation

```mermaid
graph TD
    NVS["🏭 National Vaccine Store\nControlled: 2–8°C"] --> SVS
    SVS["🏢 State Vaccine Store\nControlled: 2–8°C"] --> DVS
    DVS["🏬 District Vaccine Store\nOccasional excursions"] --> PHC
    PHC["🏥 Primary Health Centre\nFrequent power cuts\nIce pack issues"] --> OUTREACH
    OUTREACH["🏘️ Village Outreach Session\nCarrier + ice packs\nHighest risk tier"]

    style NVS fill:#22c55e,color:#fff
    style SVS fill:#22c55e,color:#fff
    style DVS fill:#f59e0b,color:#fff
    style PHC fill:#ef4444,color:#fff
    style OUTREACH fill:#7c3aed,color:#fff
```

ColdGuard was designed and tested against all three field-tier profiles (District, PHC, Outreach) with realistic excursion distributions modeled on published cold chain monitoring studies.

---

## Repository Structure

```
ColdGuard/
│
├── 🧬 core/                        Scientific engine
│   ├── arrhenius.py                Arrhenius integrator · MKT · segment attribution
│   ├── bayesian.py                 Monte Carlo uncertainty propagation
│   ├── decision.py                 USE/INVESTIGATE/DISCARD · audit hash
│   ├── vaccine_params.py           12 vaccines with derived A values
│   └── utils.py                    Parsing · validation · run_analysis pipeline
│
├── 🌐 web_app/                     Streamlit web application
│   ├── app.py                      3-state UI (input → processing → results)
│   └── components/                 input_form · results_display · charts
│
├── 📱 mobile_app/                  React Native + Expo (Android)
│   └── src/
│       ├── engine/arrhenius.js     Full offline JS engine (1000-sample MC)
│       ├── screens/                Input · Processing · Results screens
│       ├── components/             DecisionBanner · PotencyChart · Timeline
│       └── i18n/                   English · Hindi · Tamil · Bengali · Telugu · Kannada translations
│
├── 🔬 simulation/                  Protocol comparison study
│   ├── cold_chain_generator.py     District · PHC · Outreach profiles
│   └── protocol_comparison.py      ColdGuard vs MKT vs VVM · FDR/FUR metrics
│
├── ✅ validation/                  Scientific validation
│   ├── literature_validation.py    Published stability data validation
│   └── calibration_analysis.py    Coverage · RMSE · Bland-Altman
│
├── 📓 notebooks/                   Jupyter analysis
│   ├── 01_arrhenius_exploration    Rate curves for all 12 vaccines
│   ├── 02_parameter_derivation     A values from shelf-life derivation
│   ├── 03_validation_analysis      Literature comparison
│   ├── 04_simulation_study         1000-scenario protocol comparison
│   └── 05_paper_figures            All 6 publication-ready figures
│
├── 📊 data/
│   ├── raw/                        12 synthetic cold chain CSVs + demo scenario
│   ├── validation/                 Stability datasets (DPT, OPV, MMR)
│   └── parameters/                 vaccine_arrhenius_db.json
│
├── 📄 paper/                       Research paper
│   ├── main.tex                    7-section LaTeX skeleton
│   └── references.bib              WHO · ICH · literature bibliography
│
├── 📚 docs/
│   ├── SCIENCE.md                  Full Arrhenius + Bayesian derivation
│   ├── API.md                      REST API reference + Python core API
│   └── USER_GUIDE.md              Step-by-step guide for field staff
│
├── 🧪 tests/                       107 tests · all passing
│   ├── test_arrhenius.py           9 tests
│   ├── test_bayesian.py            7 tests
│   ├── test_decision.py            9 tests
│   ├── test_scenarios.py           19 scenario-level integration tests
│   ├── test_api.py                 10 tests
│   ├── test_cli.py                 17 tests
│   ├── test_i18n.py                12 tests
│   └── test_pdf_report.py          1 test
│
├── coldguard_cli.py                Command-line runner
└── .github/workflows/test.yml      CI: runs all tests on every push
```

---

## Example Output

```
ColdGuard Analysis — DPT (Diphtheria-Pertussis-Tetanus)
════════════════════════════════════════════════════════════

✅  USE  — Vaccine retains sufficient potency. Safe to administer.

  Potency estimate : 99.8%
  90% CI           : 99.2% – 100.0%
  Confidence       : 100%

  ColdGuard estimates DPT potency at 99.8% (90% CI: 99.2–100.0%).
  Minimum acceptable potency is 80%. Primary degradation source:
  11 hours at 14.3°C, accounting for 87% of total heat stress.
  It is safe to USE this vaccine.

  MKT: 11.26°C   Point estimate: 99.95%
  Audit hash: e21be4c1e394f7f0…

  Top degradation segments:
    1.0 h at mean 14.3°C  →  8.7% of total loss
    1.0 h at mean 14.3°C  →  8.7% of total loss
    1.0 h at mean 14.3°C  →  8.7% of total loss
```

---

## Roadmap — What We Can Build Next

```mermaid
timeline
    title ColdGuard Development Roadmap
    section v1.0 — Current
        Scientific engine        : Arrhenius + Monte Carlo
        Web + Mobile apps        : Streamlit + React Native
        107 passing tests         : Full test suite
        CLI + CI pipeline        : GitHub Actions
        REST API                 : FastAPI wrapper (/analyse, /vaccines, /health)
        12 vaccines              : DPT OPV MMR BCG HepB IPV Rotavirus PCV YF JE Typhoid MenA
        6 languages              : English Hindi Tamil Telugu Bengali Kannada
        Freeze damage model      : First-order kinetics accumulator
        QR code scanner          : Camera-based logger ID scan
        PDF report               : Shareable audit-trail report
    section v1.1 — Near Term
        Real validation data     : Source from WHO literature
    section v1.2 — Research
        Full paper               : Submit to journal/conference
        eVIN integration         : National cold chain API
        PyMC full Bayesian       : MCMC posterior inference
        Field pilot              : ANM usability study
    section v2.0 — Scale
        iOS app                  : iPhone support
        WhatsApp bot             : Report via WhatsApp
        IoT auto-upload          : Berlinger logger direct sync
        National dashboard       : District-level wastage analytics
```

### Priority Improvements

#### 🔬 Scientific Quality
| # | Improvement | Impact | Effort |
|---|------------|--------|--------|
| 1 | **Source real validation data** from WHO/GPV/98.07 for all 12 vaccines — replace synthetic circular validation with actual published temperature-potency pairs | 🔴 Critical for publication | High |
| 2 | ~~**Freeze damage accumulator**~~ ✅ Done — first-order freeze kinetics implemented in `core/arrhenius.py` for all freeze-sensitive vaccines | — | — |
| 3 | **Derive Eₐ independently** — use two published stability data points per vaccine: `ln(k₁/k₂) = -Eₐ/R · (1/T₁ − 1/T₂)` | 🟡 Strengthens paper | Medium |
| 4 | **PyMC full Bayesian** — replace Monte Carlo with proper MCMC posterior (PyMC already in requirements); enables formal model comparison | 🟡 Research upgrade | Medium |
| 5 | **Sensitivity analysis** — show FDR reduction holds under ±10% Eₐ variation; answers the primary reviewer question | 🟡 Paper reviewer ready | Low |

#### 📱 Feature Completeness
| # | Improvement | Impact | Effort |
|---|------------|--------|--------|
| 6 | ~~**QR code scanner**~~ ✅ Done — camera-based QR scanner in mobile app for Berlinger Fridge-tag logger IDs | — | — |
| 7 | **Hindi translation review** — `hi.js` needs review by a Hindi-speaking ANM or health worker for medical accuracy | 🟡 Accessibility | Low |
| 8 | **iOS support** — currently Expo/React Native targets Android; minor config change adds iOS | 🟢 Reach | Low |
| 9 | **WhatsApp integration** — field staff already use WhatsApp; a bot that accepts a forwarded CSV and returns a verdict removes app-install barrier | 🔴 Adoption | High |
| 10 | **Berlinger / LogTag auto-sync** — direct USB/BLE import from common Indian cold chain loggers instead of manual CSV export | 🟡 Usability | High |

#### 🏗️ Engineering
| # | Improvement | Impact | Effort |
|---|------------|--------|--------|
| 11 | **eVIN API integration** — India's Electronic Vaccine Intelligence Network has an open API; push analysis results into the national cold chain record | 🔴 National scale | High |
| 12 | **District dashboard** — Streamlit multi-page app showing batch-level wastage analytics for district cold chain officers | 🟡 Decision makers | Medium |
| 13 | **Offline PWA** — Progressive Web App wrapping so health workers without smartphones can use the web app offline from a feature phone browser | 🟡 Last-mile reach | Medium |
| 14 | **Audit trail export** — digital signature on PDF reports, exportable to HMIS/DHIS2 | 🟢 Compliance | Low |

---

### 🙋 Contributing — Find Something to Work On

Issue tables go stale, so the live list is on GitHub:

- 🌱 [**Good first issues**](https://github.com/Santhosh-zeta/ColdGuard/labels/good%20first%20issue) — small, well-scoped, with acceptance criteria
- 🆘 [**Help wanted**](https://github.com/Santhosh-zeta/ColdGuard/labels/help%20wanted) — bigger features and research questions
- 🔬 [**Science**](https://github.com/Santhosh-zeta/ColdGuard/labels/scientific) — literature data, validation, uncertainty models
- 🌐 [**Translations**](https://github.com/Santhosh-zeta/ColdGuard/labels/i18n) — add your language

Read [CONTRIBUTING.md](CONTRIBUTING.md), pick an issue, comment "I'll take this", and open a PR. A maintainer will respond within a few days.

#### 📄 Research Paper
| # | Task | Status |
|---|------|--------|
| 15 | Fill in `paper/main.tex` Results section with simulation study numbers | 🔲 Pending |
| 16 | Generate paper figures (run `notebooks/05_paper_figures.ipynb`) | 🔲 Pending |
| 17 | Submit to **Vaccine** journal or **npj Digital Medicine** | 🔲 Pending |
| 18 | Record 3-minute demo video for GitHub and supplementary | 🔲 Pending |

---

## Scientific References

| Source | Used For |
|--------|----------|
| WHO/GPV/98.07 — Galazka AM et al., *Thermostability of Vaccines*, 1998 | Eₐ values, stability data |
| WHO/IVB/06.10 — *Temperature Sensitivity of Vaccines*, 2006 | MKT methodology, VVM specifications |
| ICH Q1E — *Evaluation of Stability Data*, 2003 | Arrhenius stability framework |
| Matthias DM et al., *Vaccine* 25:20, 2007 | Freeze event prevalence |

---

## License

MIT — see [LICENSE](LICENSE). Free to use, modify, and deploy in public health programmes.

---

<div align="center">

**Built for India's 390 million doses per year.**

*ANMs shouldn't have to guess. Now they don't.*

</div>
