# ColdGuard API Reference

This document covers two interfaces:

1. **REST API** (`api/main.py`): a self-hosted FastAPI service for integrating ColdGuard into other systems.
2. **Python API** (`core/`): the scientific engine, for scripts, notebooks and the CLI.

---

# REST API

A FastAPI service that wraps the Python engine. It accepts a temperature log and a vaccine code and returns the potency estimate, a USE / INVESTIGATE / DISCARD decision, and supporting details as JSON.

- Base URL (local): `http://localhost:8000`
- Interactive docs (Swagger UI): `http://localhost:8000/docs`
- OpenAPI schema: `http://localhost:8000/openapi.json`
- Authentication: none. The service is intended for self-hosting on a trusted network. Put it behind a reverse proxy with authentication before exposing it publicly.
- Content type: `application/json` for all request bodies and responses.

## Running the server

From the repository root:

```bash
# Install dependencies (includes fastapi, uvicorn, pydantic and the engine's numerical libraries)
pip install -r requirements.txt

# Start the server with auto-reload for development
python -m uvicorn api.main:app --reload --port 8000
```

For a production-style run without auto-reload:

```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2
```

Running `python api/main.py` also starts the server, on `0.0.0.0:8000`.

Quick check that the server is up:

```bash
curl http://localhost:8000/health
# {"status":"ok","version":"1.0.0"}
```

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/` | Service name, version and a list of endpoints |
| `GET` | `/health` | Liveness check |
| `GET` | `/vaccines` | List the supported vaccines and whether each is freeze-sensitive |
| `POST` | `/analyse` | Analyse a temperature log and return potency and a decision |
| `POST` | `/batch-analyse` | Analyse many CSV logs in one request; see [`POST /batch-analyse`](#post-batch-analyse) |

---

### `GET /health`

Liveness check.

**Response `200`**

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Always `"ok"` when the service is running |
| `version` | string | API version (`"1.0.0"`) |

```bash
curl http://localhost:8000/health
```

```json
{"status": "ok", "version": "1.0.0"}
```

---

### `GET /vaccines`

Lists every vaccine code accepted by `POST /analyse`.

**Response `200`**

| Field | Type | Description |
|-------|------|-------------|
| `vaccines` | array | Vaccine objects, sorted by `key` |
| `vaccines[].key` | string | Vaccine code to pass as `vaccine` in `/analyse` |
| `vaccines[].name` | string | Full vaccine name |
| `vaccines[].freeze_sensitive` | boolean | `true` if freezing damages the vaccine |
| `count` | integer | Number of vaccines returned (12) |

```bash
curl http://localhost:8000/vaccines
```

```json
{
  "vaccines": [
    {"key": "BCG", "name": "Bacillus Calmette-Guérin", "freeze_sensitive": false},
    {"key": "DPT", "name": "DPT (Diphtheria-Pertussis-Tetanus)", "freeze_sensitive": true},
    {"key": "HepB", "name": "Hepatitis B", "freeze_sensitive": true}
  ],
  "count": 12
}
```

The list is abbreviated above. The full response contains all 12 entries.

---

### `POST /analyse`

Estimates vaccine potency from a temperature log.

**Request body**

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `vaccine` | string | yes | | Must be a key from `GET /vaccines` | Vaccine code, e.g. `"DPT"` |
| `timestamps` | array of number | yes | | At least 2 values; same length as `temperatures_c` | Unix time in seconds for each reading |
| `temperatures_c` | array of number | yes | | At least 2 values; each between -30 and 60 | Temperature in °C for each reading |
| `n_mc_samples` | integer | no | `1000` | 100 to 100000 | Number of Monte Carlo samples for uncertainty propagation |
| `initial_potency` | number | no | `1.0` | 0 to 1 | Potency fraction at manufacture (1.0 = 100%) |
| `logger_accuracy_c` | number | no | `0.5` | 0.1 to 2.0 | Temperature sensor uncertainty in °C |

Notes:
- `timestamps` are read as Unix seconds. A 1-hour logging interval is 3600 seconds apart.
- Larger `n_mc_samples` gives smoother confidence intervals but takes longer to compute.

**Response `200`**

| Field | Type | Description |
|-------|------|-------------|
| `vaccine` | string | Vaccine code that was analysed |
| `vaccine_name` | string | Full vaccine name |
| `decision_output` | object | The decision and its supporting values (see below) |
| `decision_output.decision` | string | `"USE"`, `"INVESTIGATE"` or `"DISCARD"` |
| `decision_output.estimated_potency_pct` | number | Estimated potency, in percent |
| `decision_output.ci_90` | array of 2 numbers | 90% confidence interval for potency, in percent, as `[lower, upper]` |
| `decision_output.confidence` | number | Probability that the decision is correct, from 0 to 1 |
| `decision_output.explanation` | string | Plain-language recommendation |
| `decision_output.audit_hash` | string | SHA-256 hash of the posterior summary, for audit trails |
| `potency_mean_pct` | number | Posterior mean potency (Monte Carlo) in percent. |
| `mkt_C` | number | WHO Mean Kinetic Temperature for the log, in °C |
| `point_estimate_potency` | number | Point-estimate potency as a fraction from 0 to 1 |
| `freeze_events` | array of object | Detected freezing intervals (empty if none). Each object has `start_ts`, `end_ts` and `min_temp_C`. |
| `data_quality_warnings` | array of string | Warnings about the input log, such as out-of-range values or non-monotonic timestamps |
| `logging_gaps` | array of object | Gaps in the log. Each object has `gap_start`, `gap_end` and `gap_hours`. |
| `segment_attribution` | array of object | Per-interval breakdown of degradation (see below) |

Each element of `segment_attribution`:

| Field | Type | Description |
|-------|------|-------------|
| `start_ts`, `end_ts` | number | Interval start and end, Unix seconds |
| `start_temp_C`, `end_temp_C`, `mean_temp_C` | number | Temperatures at the interval boundaries and their mean, °C |
| `duration_hours` | number | Interval length in hours |
| `degradation_contribution` | number | Absolute degradation for this interval |
| `degradation_fraction` | number | Share of total degradation; all fractions sum to 1.0 |

**Errors**

| Status | When | Body |
|--------|------|------|
| `422 Unprocessable Entity` | A field is missing, has the wrong type, or breaks a constraint above (unknown vaccine, mismatched list lengths, temperature out of range, and so on) | FastAPI validation detail, with `loc` and `msg` for each problem |
| `400 Bad Request` | The request is valid but the analysis failed inside the engine | `{"detail": "Analysis failed: <reason>"}` |

#### Example request

This example has 12 hourly readings. Readings of 14.3 °C between hours 4 and 7 represent a short excursion.

```bash
curl -X POST http://localhost:8000/analyse \
  -H "Content-Type: application/json" \
  -d '{
    "vaccine": "DPT",
    "timestamps": [1694592000, 1694595600, 1694599200, 1694602800, 1694606400, 1694610000, 1694613600, 1694617200, 1694620800, 1694624400, 1694628000, 1694631600],
    "temperatures_c": [5.0, 5.2, 4.9, 5.1, 14.3, 14.3, 14.3, 14.3, 5.0, 4.8, 5.1, 5.0],
    "n_mc_samples": 1000
  }'
```

#### Example response (abbreviated)

```json
{
  "vaccine": "DPT",
  "vaccine_name": "DPT (Diphtheria-Pertussis-Tetanus)",
  "decision_output": {
    "decision": "USE",
    "estimated_potency_pct": 99.90,
    "ci_90": [99.59, 99.998],
    "confidence": 1.0,
    "explanation": "ColdGuard estimates DPT (Diphtheria-Pertussis-Tetanus) potency at 99.9% (90% CI: 99.6–100.0%). ... It is safe to USE this vaccine.",
    "audit_hash": "3e81881e1a25310a26c33709e59f8904abd4ccfccbd975030d41653a6ef6ec8c"
  },
  "potency_mean_pct": 99.97,
  "mkt_C": 9.32,
  "point_estimate_potency": 0.99974,
  "freeze_events": [],
  "data_quality_warnings": [],
  "logging_gaps": [],
  "segment_attribution": [
    {
      "start_ts": 1694592000.0,
      "end_ts": 1694595600.0,
      "start_temp_C": 5.0,
      "end_temp_C": 5.2,
      "mean_temp_C": 5.1,
      "duration_hours": 1.0,
      "degradation_contribution": 1.31e-05,
      "degradation_fraction": 0.0512
    }
  ]
}
```

The `segment_attribution` array contains one entry per interval, so the full response has 11 entries. The values above are from a run of this example against the current code.

#### Example: invalid vaccine

```bash
curl -X POST http://localhost:8000/analyse \
  -H "Content-Type: application/json" \
  -d '{"vaccine": "XYZ", "timestamps": [1694592000, 1694595600], "temperatures_c": [5.0, 5.2]}'
```

```
HTTP/1.1 422 Unprocessable Entity
...
"msg": "Value error, Unknown vaccine. Must be one of: DPT, OPV, MMR, BCG, HepB, IPV, Rotavirus, PCV, YF, JE, Typhoid, MenA"
```

#### Example: Python client

```python
import requests

payload = {
    "vaccine": "DPT",
    "timestamps": [1694592000, 1694595600, 1694599200],
    "temperatures_c": [5.2, 6.1, 4.8],
    "n_mc_samples": 1000,
}
resp = requests.post("http://localhost:8000/analyse", json=payload, timeout=60)
resp.raise_for_status()
result = resp.json()
print(result["decision_output"]["decision"], result["decision_output"]["estimated_potency_pct"])
```

---

### `GET /`

Returns the service name, version, the path to the interactive docs, and a short list of endpoints. Useful as a quick discovery check.

---

## `POST /batch-analyse`

Analyse many lots in one request (hospital audits, CI pipelines). Each item carries CSV text with a timestamp column and a temperature column. Items are processed independently: a bad item is returned with `"status": "error"` and does not fail the batch. Up to 100 items per request.

```bash
curl -X POST http://localhost:8000/batch-analyse \
  -H "Content-Type: application/json" \
  -d '{
    "batch": [
      {"vaccine": "DPT", "label": "lot-A", "csv_data": "timestamp,temperature_celsius\n1694592000,5.0\n1694595600,6.0\n1694599200,4.5"},
      {"vaccine": "BCG", "csv_data": "timestamp,temperature_celsius\n1694592000,5.0\n1694595600,5.5"}
    ],
    "n_mc_samples": 1000
  }'
```

Response:

```json
{
  "results": [{"index": 0, "label": "lot-A", "vaccine": "DPT", "status": "ok", "analysis": {"...": "same shape as POST /analyse"}}],
  "summary": {"total": 2, "use": 2, "investigate": 0, "discard": 0, "errors": 0},
  "generated_at": "2026-11-09T07:00:00+00:00",
  "audit_id": "batch-1a2b3c4d5e6f"
}
```

## `GET /vaccines/{key}`

Returns the full kinetic parameters for one vaccine: `ea_mean_j_per_mol`, `ea_std_j_per_mol`, `a_per_hour`, `a_log_std`, `shelf_life_hours`, `ref_temp_c`, `min_potency_threshold` and `freeze_sensitive`. The key is matched case-insensitively (`dpt` and `DPT` both work). An unknown key returns `404` with the list of valid keys.

```bash
curl http://localhost:8000/vaccines/DPT
```

## `POST /export/dhis2`

Runs an analysis (same body as `POST /analyse`) plus `org_unit` (DHIS2 facility UID) and optional `period` (`YYYYMMDD`, default today UTC). Returns a DHIS2 `dataValues` payload with the data elements `CG_DECISION`, `CG_POTENCY_MEAN`, `CG_CI90_LOWER`, `CG_CI90_UPPER`, `CG_VACCINE_TYPE` and `CG_AUDIT_HASH`, ready to POST to DHIS2's `/api/dataValueSets`. The same conversion is available in Python as `core.export.to_dhis2_payload(result, org_unit, period)`. You must create matching data elements in your DHIS2 instance.

---

# Python API (`core/`)

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
- `vaccine_type` — vaccine code string, one of: `"DPT"`, `"OPV"`, `"MMR"`, `"BCG"`, `"HepB"`, `"IPV"`, `"Rotavirus"`, `"PCV"`, `"YF"`, `"JE"`, `"Typhoid"`, `"MenA"`
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
