import json
from pathlib import Path
from typing import Optional, Dict, Any

import joblib
import pandas as pd

from backend.app.business_rules import apply_business_rules


class ModelService:
    def __init__(self):
        self.model = None
        self.meta = None
        self._load_model()

    def _load_model(self):
        model_path = Path("ml/artifacts/model.pkl")
        meta_path = Path("ml/artifacts/meta.json")

        if not model_path.exists():
            raise FileNotFoundError(
                f"Model file not found at {model_path}. "
                "Please run 'python -m ml.baseline' to train the model first."
            )

        self.model = joblib.load(model_path)

        if meta_path.exists():
            with open(meta_path, 'r') as f:
                self.meta = json.load(f)
        else:
            self.meta = {}

    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if self.model is None:
            raise RuntimeError("Model not loaded. Cannot make predictions.")

        df = pd.DataFrame([input_data])
        base_prediction = self.model.predict(df)[0]

        result = apply_business_rules(float(base_prediction), input_data)

        return result

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_loaded": self.model is not None,
            "metadata": self.meta,
            "model_type": "HistGradientBoostingRegressor",
            "status": "ready" if self.model else "not_loaded"
        }


_model_service: Optional[ModelService] = None


def get_model_service() -> ModelService:
    global _model_service
    if _model_service is None:
        _model_service = ModelService()
    return _model_service


def apply_rules(cost: float, rules: dict) -> float:
    return cost
