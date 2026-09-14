"""
ColdGuard FastAPI REST wrapper for the Bayesian vaccine potency engine.

Expose the Python scientific engine as a self-hosted REST API.

Usage:
    pip install fastapi uvicorn pydantic
    python -m uvicorn api.main:app --reload --port 8000
"""

import sys
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator

# Allow importing from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.utils import run_analysis
from core.vaccine_params import VACCINE_DB
from core.decision import Decision

app = FastAPI(
    title="ColdGuard API",
    description="Kinetic-Bayesian vaccine potency estimator",
    version="1.0.0",
)


# Request/Response models
class AnalysisRequest(BaseModel):
    """Request model for POST /analyse endpoint."""
    vaccine: str = Field(..., example="DPT")
    timestamps: List[float] = Field(
        ...,
        description="Unix timestamps (seconds since epoch) for each temperature reading",
        example=[1694592000, 1694595600, 1694599200]
    )
    temperatures_c: List[float] = Field(
        ...,
        description="Temperature readings in Celsius, must match timestamps length",
        example=[5.2, 6.1, 4.8]
    )
    n_mc_samples: int = Field(1000, ge=100, le=100000, description="Monte Carlo sample count")
    initial_potency: float = Field(1.0, ge=0, le=1.0, description="Initial potency fraction (0-1)")
    logger_accuracy_c: float = Field(0.5, ge=0.1, le=2.0, description="Temperature sensor uncertainty in °C")

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
    point_estimate_potency: float
    freeze_events: List[dict]
    data_quality_warnings: List[str]
    logging_gaps: List[dict]
    segment_attribution: List[dict]

    class Config:
        allow_population_by_field_name = True

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
            potency_mean_pct=result["point_estimate_potency"] * 100,
            mkt_C=result["mkt_C"],
            point_estimate_potency=result["point_estimate_potency"],
            freeze_events=result["freeze_events"],
            data_quality_warnings=result["data_quality_warnings"],
            logging_gaps=result["logging_gaps"],
            segment_attribution=result["segment_attribution"],
        )


class VaccineInfo(BaseModel):
    """Vaccine metadata model."""
    key: str = Field(..., example="DPT")
    name: str = Field(..., example="DPT (Diphtheria-Pertussis-Tetanus)")
    freeze_sensitive: bool = Field(..., example=True)


class VaccinesResponse(BaseModel):
    """Response model for GET /vaccines endpoint."""
    vaccines: List[VaccineInfo]
    count: int


class HealthResponse(BaseModel):
    """Response model for GET /health endpoint."""
    status: str = "ok"
    version: str = "1.0.0"


# Endpoints

@app.post("/analyse", response_model=AnalysisResponse, tags=["analysis"])
async def analyse(request: AnalysisRequest):
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
        )
        return AnalysisResponse.from_analysis(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Analysis failed: {str(e)}")


@app.get("/vaccines", response_model=VaccinesResponse, tags=["metadata"])
async def get_vaccines():
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
async def health():
    """Health check endpoint."""
    return HealthResponse(status="ok", version="1.0.0")


@app.get("/", tags=["metadata"])
async def root():
    """API documentation is available at /docs."""
    return {
        "name": "ColdGuard API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "POST /analyse": "Analyze vaccine potency from temperature log",
            "GET /vaccines": "List all supported vaccines",
            "GET /health": "Health check",
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
