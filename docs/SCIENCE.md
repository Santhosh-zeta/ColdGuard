# ColdGuard — Science Reference

## 1. Why Vaccines Degrade: The Chemistry

Pharmaceutical compounds degrade through chemical reactions (oxidation, hydrolysis, etc.). Like all chemical reactions, their rate increases exponentially with temperature. This relationship, formalized by Svante Arrhenius in 1889, is the foundation of pharmaceutical stability science.

**Key insight:** Temperature determines *how fast* a drug degrades, not just *whether* it degrades. A vaccine at 14°C for 11 hours loses potency at a specific, calculable rate.

## 2. The Arrhenius Equation

### Rate constant

```
k(T) = A · exp(-Ea / RT)
```

- `k(T)` — degradation rate constant at temperature T [hr⁻¹]
- `A` — pre-exponential factor [hr⁻¹]
- `Ea` — activation energy [J/mol]
- `R` — gas constant = 8.314 J/(mol·K)
- `T` — temperature in **Kelvin** (°C + 273.15)

### First-order degradation

Most biological vaccine components degrade by first-order kinetics:

```
dC/dt = -k(T) · C
```

For a time-varying temperature trajectory T(t):

```
C(t) = C₀ · exp(-∫₀ᵗ k(T(τ)) dτ)
```

For a discrete temperature log:

```
P_remaining(%) = 100 · exp(-Σᵢ k(Tᵢ) · Δtᵢ)
```

ColdGuard evaluates this integral using the trapezoidal rule, averaging the rate constant at the endpoints of each time interval.

## 3. WHO Mean Kinetic Temperature (Baseline Comparison)

```
T_MK = (Ea/R) / { -ln[ (1/n) · Σ exp(-Ea/(R·Tᵢ)) ] }
```

MKT gives a single equivalent temperature. ColdGuard uses MKT as a baseline to compare against its full-trajectory approach.

**MKT limitations:**
- Single point estimate, no uncertainty quantification
- Cannot provide calibrated confidence intervals
- Assumes a fixed default Ea of 83 kJ/mol for all vaccines

## 4. Deriving A from Shelf-Life Specifications

When the pre-exponential factor A is not published directly, it is derived from the labeled shelf-life:

```
k_ref = -ln(P_min) / t_shelf
A = k_ref / exp(-Ea / (R · T_ref))
```

Where `t_shelf` is the shelf life in hours, `P_min` is the minimum acceptable potency at end of shelf life, and `T_ref` is the reference storage temperature.

## 5. Bayesian Uncertainty Propagation

Arrhenius parameters (Ea, A) are not known with infinite precision. Published values have confidence intervals. Logger readings have ±0.5°C sensor error.

ColdGuard propagates these uncertainties using Monte Carlo sampling (5,000 iterations):

1. Sample `Ea ~ Normal(μ_Ea, σ_Ea)` from published CI
2. Sample `ln(A) ~ Normal(ln(A_mean), σ_logA)` (log-normal, ensures positivity)
3. Add Gaussian noise to each temperature reading: `T_obs + ε`, `ε ~ Normal(0, 0.5°C)`
4. Compute remaining potency for each sample
5. Report mean, 90% credible interval, and decision probability

This gives: "92% (CI: 86–97%)" — a clinically useful confidence interval.

## 6. Decision Logic

| Condition | Decision |
|-----------|----------|
| P(potency > threshold) > 90% | USE |
| 70% < P(potency > threshold) ≤ 90% | INVESTIGATE |
| P(potency > threshold) ≤ 70% | DISCARD |

Thresholds are vaccine-specific (80% for most; 67% for OPV).

## 7. Vaccine Parameters

| Vaccine | Ea (kJ/mol) | Shelf Life | Ref Temp | Min Potency |
|---------|-------------|------------|----------|-------------|
| DPT | 83 ± 4 | 24 months | 5°C | 80% |
| OPV | 112 ± 6 | 6 months | 5°C | 67% |
| MMR | 108 ± 7 | 12 months | 5°C | 80% |
| BCG | 90 ± 5 | 12 months | 5°C | 80% |
| HepB | 70 ± 4.5 | 24 months | 5°C | 80% |
| IPV | 92 ± 5.5 | 24 months | 5°C | 80% |
| Rotavirus | 100 ± 6 | 24 months | −15°C | 80% |
| PCV | 77 ± 4 | 24 months | 5°C | 80% |

All A values derived from shelf-life specifications using the method in Section 4.

**Primary sources:**
- WHO/IVB/06.10: "Temperature Sensitivity of Vaccines"
- Galazka AM, Milstien J, Zaffran M. "Thermostability of Vaccines." WHO/GPV/98.07
- ICH Q1E: "Evaluation of Stability Data"
