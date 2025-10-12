from pydantic import BaseModel


class PredictRequest(BaseModel):
    # TODO: define request fields
    data: dict


class PredictResponse(BaseModel):
    p10: float | None = None
    p50: float | None = None
    p90: float | None = None
