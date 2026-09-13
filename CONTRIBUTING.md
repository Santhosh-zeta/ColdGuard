# Contributing to ColdGuard

Thank you for your interest in contributing! ColdGuard is a public health project — every contribution directly impacts vaccine wastage reduction and immunisation effectiveness in India and beyond.

---

## Table of Contents

- [Who Should Contribute](#who-should-contribute)
- [Ways to Contribute](#ways-to-contribute)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Scientific Contributions](#scientific-contributions)
- [Code Standards](#code-standards)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Adding a New Vaccine](#adding-a-new-vaccine)
- [Reporting Bugs](#reporting-bugs)
- [Community](#community)

---

## Who Should Contribute

We welcome contributions from:

- **Software engineers** — Python, React Native, data pipelines
- **Pharmaceutical scientists / pharmacokineticists** — Arrhenius parameters, stability data validation
- **Public health professionals** — Field usability, Hindi/regional language review, protocol alignment with WHO guidelines
- **Data scientists** — Monte Carlo methods, Bayesian inference, uncertainty quantification
- **UX designers** — Mobile UI, accessibility for low-literacy users
- **Anyone** who has ever dealt with a cold chain temperature alarm and wanted a better answer

---

## Ways to Contribute

| Type | Where |
|------|--------|
| 🐛 Bug reports | [Open an issue](https://github.com/Santhosh-zeta/ColdGuard/issues/new?template=bug_report.md) |
| 💡 Feature ideas | [Open an issue](https://github.com/Santhosh-zeta/ColdGuard/issues/new?template=feature_request.md) |
| 🧬 New vaccine parameters | [Open an issue](https://github.com/Santhosh-zeta/ColdGuard/issues/new?template=vaccine_addition.md) |
| 📖 Docs improvements | Edit any file in `docs/` and open a PR |
| 🌐 Translations | Edit `mobile_app/src/i18n/` — Hindi, Tamil, Telugu, Kannada, Bengali, etc. |
| 📊 Validation data | Add published stability data to `data/validation/` |
| 🔬 Scientific review | Review Arrhenius parameters in `core/vaccine_params.py` against primary literature |
| 💻 Code | See open issues labelled `good first issue` |

---

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm (for mobile app)
- Git

### Clone and install

```bash
git clone https://github.com/Santhosh-zeta/ColdGuard.git
cd ColdGuard

# Python engine + web app
pip install numpy scipy pandas plotly streamlit pytest

# Run tests to verify setup
PYTHONPATH=. python -m pytest tests/ -v
# Expected: 37 passed
```

### Mobile app setup

```bash
cd mobile_app
npm install
npx expo start          # opens Expo Go on your device
```

### Quick smoke test

```bash
PYTHONPATH=. python coldguard_cli.py \
    --input data/raw/demo_dpt_power_outage.csv \
    --vaccine DPT
```

---

## Project Structure

```
core/               ← Scientific engine. Most impactful contributions live here.
├── arrhenius.py    ← Arrhenius integrator, MKT, segment attribution
├── bayesian.py     ← Monte Carlo uncertainty propagation
├── decision.py     ← USE/INVESTIGATE/DISCARD logic
└── vaccine_params.py ← VaccineParams dataclass + VACCINE_DB

tests/              ← pytest suite. Every PR must keep 37/37 green.
data/raw/           ← Temperature log CSVs for testing and demo
mobile_app/src/     ← React Native app + offline JS engine
web_app/            ← Streamlit web application
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design decisions and invariants.

---

## Scientific Contributions

ColdGuard's correctness depends on accurate kinetic parameters. If you have access to primary pharmaceutical stability literature:

1. **Verification** — Check that our Eₐ values match published ranges (see `docs/SCIENCE.md`).
2. **Real validation data** — Add published temperature-potency pairs to `data/validation/` as CSV with columns `temperature_celsius,time_hours,potency_fraction,source_doi`.
3. **New vaccines** — See [Adding a New Vaccine](#adding-a-new-vaccine).
4. **Freeze damage model** — A freeze accumulation model for DPT/HepB/IPV/PCV would be a major contribution.

All scientific changes must cite a primary source (WHO document, peer-reviewed paper, or manufacturer package insert) in the PR description.

---

## Code Standards

### Python

- Format: **black** (`pip install black && black .`)
- Lint: **ruff** (`pip install ruff && ruff check .`)
- Type hints on all public functions
- No comments explaining *what* the code does — only *why* (hidden constraints, Arrhenius invariants, etc.)
- Temperature must always be in **Kelvin** inside `core/` — convert at the boundary, never mid-function

### JavaScript (mobile engine)

- The JS engine in `mobile_app/src/engine/arrhenius.js` must mirror the Python core exactly
- Any change to the Python decision logic must be reflected in the JS port
- Test by running the same scenario through both engines and comparing outputs

### Tests

- Every new feature needs a test
- Every bug fix needs a regression test
- The test suite must stay at **37/37 passing** (or more if you add tests)
- Run: `PYTHONPATH=. python -m pytest tests/ -v`

### Commit messages

Use the conventional commits style:

```
feat(bayesian): add PyMC MCMC posterior as alternative sampler
fix(arrhenius): correct temperature conversion for Rotavirus ref temp
docs(api): document potency_samples return key
test(scenarios): add BCG extended excursion scenario
data(validation): add HepB stability points from WHO/GPV/98.07
```

---

## Submitting a Pull Request

1. **Fork** the repo and create a branch: `git checkout -b feat/your-feature`
2. Make your changes with tests
3. Run the full test suite: `PYTHONPATH=. python -m pytest tests/ -v`
4. Open a PR against `main`
5. Fill in the PR template — especially the scientific justification for any parameter changes
6. A maintainer will review within 7 days

### PR checklist

- [ ] Tests pass (`37+/37`)
- [ ] New code has corresponding tests
- [ ] Scientific changes cite a primary source
- [ ] Mobile JS engine updated if Python core changed
- [ ] `docs/` updated if public API changed
- [ ] No Claude/AI attribution in commit messages — your name only

---

## Adding a New Vaccine

To add a vaccine not currently in `VACCINE_DB`:

1. Open an issue using the [Vaccine Addition template](https://github.com/Santhosh-zeta/ColdGuard/issues/new?template=vaccine_addition.md) with the primary source citation
2. Add the `VaccineParams` entry to `core/vaccine_params.py` — derive A from shelf-life using `derive_A_from_shelf_life()`
3. Add the matching entry to `mobile_app/src/engine/arrhenius.js` `VACCINE_DB`
4. Add at least one scenario CSV to `data/raw/`
5. Add at least one test in `tests/test_scenarios.py`
6. Document the parameter source in the PR

See [ARCHITECTURE.md — Adding a new vaccine](ARCHITECTURE.md) for the exact steps.

---

## Reporting Bugs

Use the [bug report template](https://github.com/Santhosh-zeta/ColdGuard/issues/new?template=bug_report.md). Include:

- Your OS, Python version
- The exact command / input that triggered the bug
- The temperature CSV if the bug is scenario-specific (anonymise if needed)
- Expected vs actual output

For **scientific bugs** (wrong potency calculation, wrong decision), this is critical — please include the temperature log and cite what the correct result should be.

---

## Community

- Be welcoming and respectful — see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- This is a public health project. We prioritise contributions that directly improve field usability for ANMs and cold chain officers in low-resource settings.
- Questions? Open a [GitHub Discussion](https://github.com/Santhosh-zeta/ColdGuard/discussions) or an issue.

---

## Recognition

All contributors are credited in [CHANGELOG.md](CHANGELOG.md). Scientific contributors (those who add or verify kinetic parameters) will be acknowledged in the research paper acknowledgements section.
