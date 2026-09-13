## What does this PR do?

<!-- One-paragraph summary of the change. Be specific about what component is affected. -->

## Type of Change

- [ ] 🐛 Bug fix
- [ ] ✨ New feature
- [ ] 🧬 Scientific update (kinetic parameters, decision logic, validation data)
- [ ] 📱 Mobile app change
- [ ] 🌐 Web app change
- [ ] 📖 Documentation
- [ ] 🧪 Test addition / improvement
- [ ] 🔧 Build / CI / tooling

## Scientific Justification (if applicable)

<!-- For any change to core/, vaccine_params.py, or decision thresholds:
     cite the primary source (DOI, WHO document number, or manufacturer insert).
     Explain WHY the current value was wrong or could be improved. -->

**Source:** 

## Testing

- [ ] All 37 existing tests pass (`PYTHONPATH=. python -m pytest tests/ -v`)
- [ ] New tests added for new functionality
- [ ] Regression test added for bug fix
- [ ] Tested CLI: `PYTHONPATH=. python coldguard_cli.py --input data/raw/demo_dpt_power_outage.csv --vaccine DPT`
- [ ] Mobile JS engine updated if Python core changed (`mobile_app/src/engine/arrhenius.js`)
- [ ] Documentation updated if public API changed

## Screenshots / Output (if applicable)

<!-- For web or mobile changes, attach a screenshot.
     For CLI or API changes, paste the relevant output. -->

```
# Paste output here
```

## Checklist

- [ ] My commit messages follow the conventional commits style (see CONTRIBUTING.md)
- [ ] My name (not Claude's) is the author on all commits
- [ ] No hardcoded paths, secrets, or personal data
- [ ] No breaking changes to the public API in `core/` (or if there are, they are documented)
