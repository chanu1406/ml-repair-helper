from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.app.schemas import (
    PredictRequest,
    PredictResponse,
    ModelInfoResponse,
    HealthResponse
)
from backend.app.service import get_model_service


app = FastAPI(
    title="RepairHelper API",
    description="API for predicting auto repair costs and claim decisions",
    version="1.0.0"
)

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


@app.post("/predict", response_model=PredictResponse, tags=["Predictions"])
def predict_cost(request: PredictRequest):
    try:
        model_service = get_model_service()
        predicted_cost = model_service.predict(request.features)

        return PredictResponse(
            predicted_cost=predicted_cost,
            model_version="baseline-v1"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction error: {str(e)}"
        )


@app.post("/predict/cost", response_model=PredictResponse, tags=["Predictions"])
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
