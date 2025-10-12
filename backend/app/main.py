from fastapi import FastAPI

app = FastAPI(title="RepairHelper API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict/cost")
def predict_cost(payload: dict):
    """Placeholder endpoint. Returns minimal structure."""
    return {"p10": None, "p50": None, "p90": None}


@app.post("/predict/decision")
def predict_decision(payload: dict):
    return {"p_approve": None}
