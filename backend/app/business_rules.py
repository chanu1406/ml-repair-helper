from typing import Dict, Any
from backend.app.enhanced_valuation import (
    estimate_repair_cost_by_severity,
    apply_regional_adjustment
)
from backend.app.valuation_service import get_vehicle_value


def apply_business_rules(
    base_prediction: float,
    features: Dict[str, Any]
) -> Dict[str, Any]:

    auto_make = features.get("auto_make", "Toyota")
    auto_year = features.get("auto_year", 2010)
    auto_model = features.get("auto_model", "")
    auto_mileage = features.get("auto_mileage")  # New field
    vin = features.get("vin")  # New field - VIN for accurate valuation
    incident_severity = features.get("incident_severity", "Minor Damage")
    collision_type = features.get("collision_type", "")
    state = features.get("policy_state", features.get("incident_state", "OH"))

    # NEW: Use real market data valuation service
    # Falls back to hardcoded model if no market data available
    vehicle_value, value_metadata = get_vehicle_value(
        vin=vin,
        make=auto_make,
        model=auto_model,
        year=auto_year,
        mileage=auto_mileage,
        state=state
    )

    severity_cost, severity_reasoning = estimate_repair_cost_by_severity(
        vehicle_value,
        incident_severity,
        collision_type
    )

    adjusted_prediction, regional_reasoning = apply_regional_adjustment(severity_cost, state)

    model_confidence_range = abs(base_prediction - adjusted_prediction) / adjusted_prediction
    if model_confidence_range < 0.15:
        confidence = "high"
    elif model_confidence_range < 0.35:
        confidence = "medium"
    else:
        confidence = "low"

    reasoning = [severity_reasoning]
    if regional_reasoning:
        reasoning.append(regional_reasoning)

    if abs(base_prediction - adjusted_prediction) > 2000:
        reasoning.append(f"Base ML model predicted ${base_prediction:,.0f}, adjusted to ${adjusted_prediction:,.0f}")

    adjusted_prediction = max(adjusted_prediction, 500)

    bodily_injuries = features.get("bodily_injuries", 0)
    if bodily_injuries and bodily_injuries > 0:
        injury_cost = bodily_injuries * 5000
        adjusted_prediction += injury_cost
        reasoning.append(f"Added ${injury_cost:,.0f} for {bodily_injuries} bodily injury/injuries")

    return {
        "predicted_cost": adjusted_prediction,
        "base_model_prediction": base_prediction,
        "estimated_vehicle_value": vehicle_value,
        "confidence": confidence,
        "reasoning": reasoning,
        "valuation_details": value_metadata
    }
