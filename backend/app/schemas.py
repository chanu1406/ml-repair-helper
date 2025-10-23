from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    features: Dict[str, Any] = Field(
        ...,
        example={
            "months_as_customer": 328,
            "age": 48,
            "policy_state": "OH",
            "policy_deductable": 1000,
            "policy_annual_premium": 1406.91,
            "insured_sex": "MALE",
            "insured_education_level": "MD",
            "incident_type": "Single Vehicle Collision",
            "collision_type": "Side Collision",
            "incident_severity": "Major Damage",
            "authorities_contacted": "Police",
            "auto_make": "Saab",
            "auto_model": "92x",
            "auto_year": 2004,
            "auto_mileage": 75000,  # NEW: Vehicle mileage
            "vin": "1G1ZD5ST4JF123456",  # NEW: Vehicle VIN (optional but recommended)
            "number_of_vehicles_involved": 1,
            "bodily_injuries": 1,
            "witnesses": 2
        }
    )

    class Config:
        json_schema_extra = {
            "example": {
                "features": {
                    "months_as_customer": 328,
                    "age": 48,
                    "policy_state": "OH",
                    "policy_deductable": 1000,
                    "incident_type": "Single Vehicle Collision",
                    "auto_make": "Saab",
                    "auto_year": 2004
                }
            }
        }


class PredictResponse(BaseModel):
    predicted_cost: float
    model_version: Optional[str] = None
    confidence: Optional[str] = None


class ModelInfoResponse(BaseModel):
    model_loaded: bool
    model_type: str
    status: str
    metadata: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str
