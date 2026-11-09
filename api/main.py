"""
ColdGuard FastAPI REST wrapper for the Bayesian vaccine potency engine.

Expose the Python scientific engine as a self-hosted REST API.

Usage:
    pip install fastapi uvicorn pydantic
    python -m uvicorn api.main:app --reload --port 8000
"""

import io
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Allow importing from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import __version__
from core.export import to_dhis2_payload
from core.utils import parse_csv_log, run_analysis
from core.vaccine_params import VACCINE_DB

app = FastAPI(
    title="ColdGuard API",
    description="Kinetic-Bayesian vaccine potency estimator",
    version=__version__,
)


# Request/Response models
class AnalysisRequest(BaseModel):
    """Request model for POST /analyse endpoint."""
    vaccine: str = Field(..., json_schema_extra={"example": "DPT"})
    timestamps: List[float] = Field(
        ...,
        description="Unix timestamps (seconds since epoch) for each temperature reading",
        json_schema_extra={"example": [1694592000, 1694595600, 1694599200]}
    )
    temperatures_c: List[float] = Field(
        ...,
        description="Temperature readings in Celsius, must match timestamps length",
        json_schema_extra={"example": [5.2, 6.1, 4.8]}
    )
    n_mc_samples: int = Field(1000, ge=100, le=100000, description="Monte Carlo sample count")
    initial_potency: float = Field(1.0, ge=0, le=1.0, description="Initial potency fraction (0-1)")
    logger_accuracy_c: float = Field(0.5, ge=0.1, le=2.0, description="Temperature sensor uncertainty in °C")
    seed: Optional[int] = Field(None, ge=0, description="RNG seed for reproducible results")

    @field_validator('vaccine')
    @classmethod
    def validate_vaccine(cls, v):
        if v not in VACCINE_DB:
            raise ValueError(f"Unknown vaccine. Must be one of: {', '.join(VACCINE_DB.keys())}")
        return v

    @field_validator('temperatures_c')
    @classmethod
    def validate_temps(cls, v):
        if len(v) < 2:
            raise ValueError("At least 2 temperature readings required")
        if any(t < -30 or t > 60 for t in v):
            raise ValueError("Temperature must be between -30°C and 60°C")
        return v

    @field_validator('timestamps')
    @classmethod
    def validate_timestamps(cls, v):
        if len(v) < 2:
            raise ValueError("At least 2 timestamps required")
        if any(b <= a for a, b in zip(v, v[1:])):
            raise ValueError("timestamps must be strictly increasing")
        return v

    @model_validator(mode='after')
    def validate_match(self):
        if len(self.timestamps) != len(self.temperatures_c):
            raise ValueError("timestamps and temperatures_c must have matching lengths")
        return self


class DecisionOutput(BaseModel):
    """Decision output model."""
    decision: str = Field(..., description="USE | INVESTIGATE | DISCARD")
    estimated_potency_pct: float = Field(..., description="Estimated potency as percentage")
    ci_90: tuple = Field(..., description="90% confidence interval as [lower, upper]")
    confidence: float = Field(..., description="Confidence value (0-1)")
    explanation: str = Field(..., description="Natural language explanation")
    audit_hash: str = Field(..., description="Audit trail hash")


class AnalysisResponse(BaseModel):
    """Response model for POST /analyse endpoint."""
    vaccine: str
    vaccine_name: str
    decision_output: DecisionOutput
    potency_mean_pct: float
    mkt_c: float = Field(..., alias="mkt_C", description="Mean Kinetic Temperature in Celsius")
    model_config = ConfigDict(populate_by_name=True)
    point_estimate_potency: float
    seed: Optional[int] = None
    freeze_events: List[dict]
    data_quality_warnings: List[str]
    logging_gaps: List[dict]
    segment_attribution: List[dict]

    @staticmethod
    def from_analysis(result: dict) -> "AnalysisResponse":
        """Convert core.utils.run_analysis output to response model."""
        dec_out = result["decision_output"]
        return AnalysisResponse(
            vaccine=result["vaccine_type"],
            vaccine_name=result["vaccine_name"],
            decision_output=DecisionOutput(
                decision=dec_out.decision.value,
                estimated_potency_pct=dec_out.estimated_potency_pct,
                ci_90=dec_out.ci_90,
                confidence=float(dec_out.confidence),
                explanation=dec_out.natural_language_explanation,
                audit_hash=dec_out.audit_hash,
            ),
            potency_mean_pct=dec_out.estimated_potency_pct,
            mkt_C=result["mkt_C"],
            point_estimate_potency=result["point_estimate_potency"],
            seed=result.get("seed"),
            freeze_events=result["freeze_events"],
            data_quality_warnings=result["data_quality_warnings"],
            logging_gaps=result["logging_gaps"],
            segment_attribution=result["segment_attribution"],
        )


class VaccineInfo(BaseModel):
    """Vaccine metadata model."""
    key: str = Field(..., json_schema_extra={"example": "DPT"})
    name: str = Field(..., json_schema_extra={"example": "DPT (Diphtheria-Pertussis-Tetanus)"})
    freeze_sensitive: bool = Field(..., json_schema_extra={"example": True})


class VaccinesResponse(BaseModel):
    """Response model for GET /vaccines endpoint."""
    vaccines: List[VaccineInfo]
    count: int


class HealthResponse(BaseModel):
    """Response model for GET /health endpoint."""
    status: str = "ok"
    version: str = __version__


# Endpoints

@app.post("/analyse", response_model=AnalysisResponse, tags=["analysis"])
def analyse(request: AnalysisRequest):
    """
    Analyze vaccine potency from temperature log.

    Takes a temperature log and vaccine type, returns estimated potency,
    decision (USE/INVESTIGATE/DISCARD), confidence, and explanations.
    """
    try:
        result = run_analysis(
            vaccine_type=request.vaccine,
            timestamps=request.timestamps,
            temperatures_C=request.temperatures_c,
            initial_potency=request.initial_potency,
            n_mc_samples=request.n_mc_samples,
            logger_accuracy_C=request.logger_accuracy_c,
            seed=request.seed,
        )
        return AnalysisResponse.from_analysis(result)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Invalid analysis request: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Analysis failed: {str(e)}")


class BatchItem(BaseModel):
    """One vaccine lot in a batch request."""
    vaccine: str = Field(..., json_schema_extra={"example": "DPT"})
    csv_data: str = Field(
        ...,
        description="CSV text with a timestamp column and a temperature column",
    )
    initial_potency: float = Field(1.0, ge=0, le=1.0)
    label: Optional[str] = Field(None, description="Optional lot / facility label echoed back")


class BatchRequest(BaseModel):
    """Request model for POST /batch-analyse."""
    batch: List[BatchItem] = Field(..., min_length=1, max_length=100)
    n_mc_samples: int = Field(1000, ge=100, le=100000)
    logger_accuracy_c: float = Field(0.5, ge=0.1, le=2.0)


class BatchResponse(BaseModel):
    results: List[dict]
    summary: dict
    generated_at: str
    audit_id: str


def _analyse_batch_item(index: int, item: BatchItem, req: BatchRequest) -> dict:
    """Analyse one batch item, capturing errors per item instead of failing the batch."""
    base = {"index": index, "label": item.label, "vaccine": item.vaccine}
    if item.vaccine not in VACCINE_DB:
        return {**base, "status": "error",
                "error": f"Unknown vaccine. Must be one of: {', '.join(VACCINE_DB)}"}
    try:
        ts, temps = parse_csv_log(io.StringIO(item.csv_data))
        if len(ts) < 2:
            raise ValueError("At least 2 temperature readings required")
        result = run_analysis(
            vaccine_type=item.vaccine,
            timestamps=ts,
            temperatures_C=temps,
            initial_potency=item.initial_potency,
            n_mc_samples=req.n_mc_samples,
            logger_accuracy_C=req.logger_accuracy_c,
        )
        analysis = AnalysisResponse.from_analysis(result).model_dump(by_alias=True)
        return {**base, "status": "ok", "analysis": analysis}
    except Exception as e:
        return {**base, "status": "error", "error": str(e)}


@app.post("/batch-analyse", response_model=BatchResponse, tags=["analysis"])
def batch_analyse(request: BatchRequest):
    """
    Analyse many CSV temperature logs in one request.

    Each item is processed independently; a bad item is reported with
    ``status: "error"`` and does not fail the rest of the batch.
    """
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(
            lambda pair: _analyse_batch_item(pair[0], pair[1], request),
            enumerate(request.batch),
        ))
    summary = {"total": len(results), "use": 0, "investigate": 0, "discard": 0, "errors": 0}
    for r in results:
        if r["status"] == "ok":
            summary[r["analysis"]["decision_output"]["decision"].lower()] += 1
        else:
            summary["errors"] += 1
    return BatchResponse(
        results=results,
        summary=summary,
        generated_at=datetime.now(timezone.utc).isoformat(),
        audit_id=f"batch-{uuid.uuid4().hex[:12]}",
    )


class DHIS2ExportRequest(AnalysisRequest):
    """Analysis request plus DHIS2 reporting context."""
    org_unit: str = Field(..., min_length=1, description="DHIS2 organisation unit UID")
    period: Optional[str] = Field(None, pattern=r"^\d{8}$", description="YYYYMMDD; defaults to today (UTC)")


@app.post("/export/dhis2", tags=["integrations"])
def export_dhis2(request: DHIS2ExportRequest):
    """Run an analysis and return a DHIS2-compatible ``dataValues`` payload."""
    try:
        result = run_analysis(
            vaccine_type=request.vaccine,
            timestamps=request.timestamps,
            temperatures_C=request.temperatures_c,
            initial_potency=request.initial_potency,
            n_mc_samples=request.n_mc_samples,
            logger_accuracy_C=request.logger_accuracy_c,
            seed=request.seed,
        )
        return to_dhis2_payload(result, request.org_unit, request.period)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Invalid export request: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Export failed: {str(e)}")


@app.get("/vaccines", response_model=VaccinesResponse, tags=["metadata"])
def get_vaccines():
    """
    List all supported vaccines with metadata.

    Returns the 12 UIP-approved vaccines that ColdGuard can analyze.
    """
    vaccines = [
        VaccineInfo(
            key=key,
            name=params.name,
            freeze_sensitive=params.freeze_sensitive,
        )
        for key, params in VACCINE_DB.items()
    ]
    return VaccinesResponse(
        vaccines=sorted(vaccines, key=lambda v: v.key),
        count=len(vaccines),
    )


@app.get("/health", response_model=HealthResponse, tags=["metadata"])
def health():
    """Health check endpoint."""
    return HealthResponse(status="ok", version=__version__)


@app.get("/", tags=["metadata"])
async def root():
    """API documentation is available at /docs."""
    return {
        "name": "ColdGuard API",
        "version": __version__,
        "docs": "/docs",
        "endpoints": {
            "POST /analyse": "Analyze vaccine potency from temperature log",
            "POST /batch-analyse": "Analyse multiple CSV logs in one request",
            "GET /vaccines": "List all supported vaccines",
            "GET /health": "Health check",
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
