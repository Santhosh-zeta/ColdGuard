# ColdGuard API Reference

## Top-level function

### `core.utils.run_analysis`

```python
run_analysis(
    vaccine_type: str,
    timestamps: np.ndarray,
    temperatures_C: np.ndarray,
    initial_potency: float = 1.0,
    n_mc_samples: int = 5000,
    logger_accuracy_C: float = 0.5,
) -> dict
```

Run the full ColdGuard pipeline: Arrhenius integration → Monte Carlo uncertainty propagation → decision.

**Parameters:**
- `vaccine_type` — vaccine code string, one of: `"DPT"`, `"OPV"`, `"MMR"`, `"BCG"`, `"HepB"`, `"IPV"`, `"Rotavirus"`, `"PCV"`
- `timestamps` — Unix timestamps in seconds (float64 ndarray), monotonically increasing
- `temperatures_C` — temperature readings in Celsius (float64 ndarray), same length as `timestamps`
- `initial_potency` — fraction of initial potency at manufacturing date (default 1.0 = 100%)
- `n_mc_samples` — number of Monte Carlo samples (default 5000, use 1000 for mobile)
- `logger_accuracy_C` — logger measurement uncertainty in °C (default 0.5)

**Returns dict with keys:**
- `vaccine_type` — str
- `vaccine_name` — str (full name)
- `data_quality_warnings` — list[str]
- `freeze_events` — list[dict] with `start_ts`, `end_ts`, `min_temp_C`
- `logging_gaps` — list[dict] with `gap_start`, `gap_end`, `gap_hours`
- `point_estimate_potency` — float, potency using nominal Ea/A (no uncertainty)
- `mkt_C` — float, WHO Mean Kinetic Temperature in °C
- `mkt_potency_estimate` — float, potency estimated via MKT baseline
- `segment_attribution` — list[dict] (see below)
- `posterior_summary` — dict (see below)
- `decision_output` — `DecisionOutput` dataclass
- `potency_samples` — np.ndarray of n_mc_samples potency values

---

## Data classes

### `VaccineParams`

```python
@dataclass
class VaccineParams:
    name: str                    # Full vaccine name
    Ea_mean: float               # Mean activation energy [J/mol]
    Ea_std: float                # Std deviation of Ea [J/mol]
    A: float                     # Pre-exponential factor [hr⁻¹]
    A_log_std: float             # Log-scale std of A
    shelf_life_hours: float      # Shelf life at ref_temp_K
    ref_temp_K: float            # Reference temperature [K]
    min_potency_threshold: float # Minimum acceptable potency fraction
    freeze_sensitive: bool       # Whether freezing damages this vaccine
```

### `DecisionOutput`

```python
@dataclass
class DecisionOutput:
    decision: Decision                      # USE, INVESTIGATE, or DISCARD
    confidence: float                       # Probability decision is correct [0–1]
    estimated_potency_pct: float            # Mean potency [%]
    ci_90: tuple[float, float]             # (lower, upper) 90% CI [%]
    primary_degradation_cause: str          # Human-readable cause description
    natural_language_explanation: str       # Full recommendation text
    audit_hash: str                         # SHA256 of posterior summary
```

### `Decision` (enum)

```python
class Decision(Enum):
    USE = "USE"
    INVESTIGATE = "INVESTIGATE"
    DISCARD = "DISCARD"
```

---

## Posterior summary dict

Keys returned by `compute_posterior_summary(samples)`:

| Key | Description |
|-----|-------------|
| `mean` | Mean potency fraction |
| `median` | Median potency fraction |
| `ci_90_lower` | 5th percentile |
| `ci_90_upper` | 95th percentile |
| `ci_95_lower` | 2.5th percentile |
| `ci_95_upper` | 97.5th percentile |
| `prob_above_80pct` | P(potency > 80%) |
| `prob_above_67pct` | P(potency > 67%) |
| `std` | Standard deviation |

---

## Segment attribution list

Each element of `segment_attribution` is a dict:

| Key | Description |
|-----|-------------|
| `start_ts` | Segment start (Unix seconds) |
| `end_ts` | Segment end (Unix seconds) |
| `start_temp_C` | Temperature at start [°C] |
| `end_temp_C` | Temperature at end [°C] |
| `mean_temp_C` | Average temperature [°C] |
| `duration_hours` | Duration [hours] |
| `degradation_contribution` | Absolute degradation D for this segment |
| `degradation_fraction` | Fraction of total D (sums to 1.0) |

---

## Parsing utilities

### `parse_csv_log(filepath) -> (timestamps, temperatures_C)`

Parse a CSV with columns `timestamp` (ISO-8601 or Unix) and `temperature_celsius`.

### `parse_json_log(data_dict) -> (timestamps, temperatures_C)`

Parse the JSON input schema:
```json
{
  "vaccine_type": "DPT",
  "temperature_log": [
    {"timestamp": "2024-09-01T08:00:00", "temperature_celsius": 4.2}
  ]
}
```

### `validate_temperature_log(timestamps, temperatures) -> list[str]`

Returns a list of warning strings for: out-of-range temperatures, non-monotonic timestamps, large gaps.

---

## Low-level functions

### `arrhenius_k(T_kelvin, Ea, A) -> float`
Compute rate constant at temperature T_kelvin [K].

### `integrate_degradation(timestamps, temperatures_C, Ea, A) -> float`
Compute cumulative degradation integral using trapezoidal rule. Returns D such that `P = exp(-D)`.

### `compute_mkt(temperatures_C, Ea=83000) -> float`
Compute WHO Mean Kinetic Temperature in °C.

### `derive_A_from_shelf_life(shelf_life_hours, T_ref_C, min_potency, Ea) -> float`
Derive pre-exponential A from labeled shelf-life specification.

### `monte_carlo_potency_distribution(timestamps, temperatures_C, vaccine_params, n_samples, ...) -> np.ndarray`
Run Monte Carlo uncertainty propagation. Returns array of potency samples.
