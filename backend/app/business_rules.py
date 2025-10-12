from typing import Dict, Any


VEHICLE_BASE_VALUES = {
    "BMW": 45000,
    "Mercedes": 48000,
    "Audi": 42000,
    "Lexus": 43000,
    "Tesla": 50000,
    "Porsche": 65000,
    "Chevrolet": 28000,
    "Ford": 27000,
    "Toyota": 26000,
    "Honda": 25000,
    "Nissan": 24000,
    "Dodge": 26000,
    "Jeep": 30000,
    "Subaru": 27000,
    "Mazda": 24000,
    "Volkswagen": 26000,
    "Hyundai": 23000,
    "Kia": 22000,
    "Saab": 25000,
    "Suburu": 27000,
    "Accura": 35000,
}


def estimate_vehicle_value(make: str, year: int, model: str = None) -> float:
    base_value = VEHICLE_BASE_VALUES.get(make, 25000)

    current_year = 2024
    age = current_year - year

    if age < 0:
        age = 0

    depreciation_rate = 0.15 if age <= 1 else 0.12
    annual_depreciation = min(age, 10)

    depreciation_factor = (1 - depreciation_rate) ** annual_depreciation
    estimated_value = base_value * depreciation_factor

    estimated_value = max(estimated_value, 2000)

    if model and any(x in model.upper() for x in ["M3", "M4", "M5", "AMG", "RS", "GT", "TURBO", "S-LINE"]):
        estimated_value *= 1.5

    return estimated_value


def apply_business_rules(
    base_prediction: float,
    features: Dict[str, Any]
) -> Dict[str, Any]:

    auto_make = features.get("auto_make", "Toyota")
    auto_year = features.get("auto_year", 2010)
    auto_model = features.get("auto_model", "")
    incident_severity = features.get("incident_severity", "Minor Damage")

    vehicle_value = estimate_vehicle_value(auto_make, auto_year, auto_model)

    adjusted_prediction = base_prediction
    confidence = "medium"
    reasoning = []

    if incident_severity == "Total Loss":
        adjusted_prediction = vehicle_value * 0.85
        confidence = "high"
        reasoning.append(f"Total loss adjusted to vehicle value (~{vehicle_value:,.0f})")

    elif incident_severity == "Major Damage":
        if base_prediction < vehicle_value * 0.2:
            adjusted_prediction = vehicle_value * 0.35
            reasoning.append(f"Major damage increased to 35% of vehicle value")
        elif base_prediction > vehicle_value * 0.8:
            adjusted_prediction = vehicle_value * 0.6
            reasoning.append(f"Major damage capped at 60% of vehicle value")

    elif incident_severity == "Minor Damage":
        if base_prediction > vehicle_value * 0.4:
            adjusted_prediction = vehicle_value * 0.25
            reasoning.append(f"Minor damage capped at 25% of vehicle value")

    elif incident_severity == "Trivial Damage":
        if base_prediction > vehicle_value * 0.15:
            adjusted_prediction = vehicle_value * 0.08
            reasoning.append(f"Trivial damage capped at 8% of vehicle value")

    if adjusted_prediction > vehicle_value * 1.2:
        adjusted_prediction = vehicle_value * 0.9
        reasoning.append(f"Repair cost capped near total vehicle value")

    adjusted_prediction = max(adjusted_prediction, 500)

    return {
        "predicted_cost": adjusted_prediction,
        "base_model_prediction": base_prediction,
        "estimated_vehicle_value": vehicle_value,
        "confidence": confidence,
        "reasoning": reasoning if reasoning else ["Standard model prediction"]
    }
