# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x (current) | ✅ Yes |

## Scope

ColdGuard is a decision support tool for vaccine cold chain management. Security is important here for two reasons:

1. **Data integrity** — Temperature logs and analysis results feed into vaccine discard/use decisions. Tampered inputs or outputs could affect patient safety.
2. **Audit trail** — ColdGuard generates SHA-256 audit hashes for each analysis. Any vulnerability that allows hash collision or spoofing is a serious issue.

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub Issues.**

Instead, report them by emailing: **iamsanthosh2425@gmail.com**

Include in your report:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)

You will receive an acknowledgement within 48 hours and a full response within 7 days.

## What Qualifies as a Security Issue

- Input injection via malicious CSV/JSON temperature logs
- Hash collision or spoofing in the audit hash (`core/decision.py`)
- Any vulnerability that could cause ColdGuard to output a USE decision for a genuinely degraded vaccine (False Use Rate manipulation)
- Dependency vulnerabilities in numpy, scipy, pandas, streamlit, or React Native packages

## What Does Not Qualify

- Bugs that cause incorrect potency estimates due to wrong kinetic parameters (use a regular bug report)
- UI/UX issues in the web or mobile app
- Performance issues

## Dependency Updates

Dependabot is configured to automatically open PRs for dependency security updates. See [.github/dependabot.yml](.github/dependabot.yml).
