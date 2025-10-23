from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from backend.app.schemas import (
    PredictRequest,
    PredictResponse,
    ModelInfoResponse,
    HealthResponse
)
from backend.app.service import get_model_service
from backend.app.database.session import init_db
from backend.app.valuation_service import get_vehicle_value
from backend.app.nhtsa_service import decode_vin


app = FastAPI(
    title="RepairHelper API",
    description="API for predicting auto repair costs and claim decisions with real-time vehicle valuation",
    version="2.0.0"
)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    """Initialize database tables on startup"""
    try:
        init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health():
    return {"status": "ok"}


@app.get("/model-info", response_model=ModelInfoResponse, tags=["Model"])
def get_model_info():
    try:
        model_service = get_model_service()
        return model_service.get_model_info()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving model info: {str(e)}"
        )


@app.post("/predict", tags=["Predictions"])
def predict_cost(request: PredictRequest):
    try:
        model_service = get_model_service()
        result = model_service.predict(request.features)

        return {
            "predicted_cost": result["predicted_cost"],
            "base_model_prediction": result.get("base_model_prediction"),
            "estimated_vehicle_value": result.get("estimated_vehicle_value"),
            "confidence": result.get("confidence", "medium"),
            "reasoning": result.get("reasoning", []),
            "model_version": "baseline-v1-enhanced"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction error: {str(e)}"
        )


@app.post("/predict/cost", tags=["Predictions"])
def predict_cost_legacy(payload: dict):
    features = payload.get("features", payload)
    request = PredictRequest(features=features)
    return predict_cost(request)


@app.post("/predict/decision", tags=["Predictions"])
def predict_decision(payload: dict):
    return {
        "recommendation": "coming_soon",
        "message": "Decision logic not yet implemented"
    }


@app.get("/vehicle/decode/{vin}", tags=["Vehicle"])
def decode_vehicle_vin(vin: str):
    """Decode a VIN using NHTSA API"""
    try:
        if len(vin) != 17:
            raise HTTPException(status_code=400, detail="VIN must be 17 characters")

        vehicle_data = decode_vin(vin)
        return {
            "vin": vin,
            "vehicle_data": vehicle_data,
            "source": "NHTSA"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"VIN decode error: {str(e)}")


@app.get("/vehicle/value", tags=["Vehicle"])
def get_vehicle_valuation(
    vin: Optional[str] = None,
    make: Optional[str] = None,
    model: Optional[str] = None,
    year: Optional[int] = None,
    mileage: Optional[int] = None,
    state: Optional[str] = None
):
    """Get vehicle valuation using market data"""
    try:
        if not vin and not (make and model and year):
            raise HTTPException(
                status_code=400,
                detail="Must provide either VIN or make/model/year"
            )

        value, metadata = get_vehicle_value(
            vin=vin,
            make=make,
            model=model,
            year=year,
            mileage=mileage,
            state=state
        )

        return {
            "estimated_value": value,
            "metadata": metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Valuation error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
