---
name: Bug Report
about: Report incorrect behavior, wrong calculations, or crashes
title: "[BUG] "
labels: ["bug"]
assignees: []
---

## Description

<!-- Clear description of what went wrong -->

## Steps to Reproduce

```bash
# Paste the exact command or code that triggered the bug
PYTHONPATH=. python coldguard_cli.py --input ... --vaccine ...
```

## Temperature Log

<!-- If the bug is scenario-specific, paste the CSV content or attach the file.
     Anonymise any patient/location data. -->

<details>
<summary>temperature_log.csv</summary>

```
timestamp,temperature_celsius
2024-09-01 08:00:00,4.2
...
```

</details>

## Expected Behavior

<!-- What should have happened? If this is a scientific bug, cite the expected potency/decision and its source. -->

## Actual Behavior

<!-- What did ColdGuard output? Paste the full output. -->

```
# Paste output here
```

## Environment

- OS: <!-- e.g. Ubuntu 22.04, macOS 14, Windows 11 -->
- Python version: <!-- e.g. 3.11.5 -->
- ColdGuard version / commit: <!-- git log --oneline -1 -->
- Interface: <!-- CLI / Web App / Mobile / Python API -->

## Scientific Context (if applicable)

<!-- If this is a wrong potency calculation, what does the correct answer appear to be, and based on what source? -->

## Additional Context

<!-- Any other relevant information -->
