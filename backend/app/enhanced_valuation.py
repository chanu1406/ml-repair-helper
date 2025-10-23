from typing import Dict, Any, Tuple


VEHICLE_MSRP_2024 = {
    "BMW": {"base": 45000, "luxury_factor": 1.8, "depreciation": "slow"},
    "Mercedes": {"base": 50000, "luxury_factor": 1.9, "depreciation": "slow"},
    "Audi": {"base": 43000, "luxury_factor": 1.7, "depreciation": "slow"},
    "Lexus": {"base": 44000, "luxury_factor": 1.6, "depreciation": "very_slow"},
    "Tesla": {"base": 48000, "luxury_factor": 1.5, "depreciation": "moderate"},
    "Porsche": {"base": 70000, "luxury_factor": 2.5, "depreciation": "slow"},
    "Chevrolet": {"base": 30000, "luxury_factor": 1.0, "depreciation": "fast"},
    "Ford": {"base": 32000, "luxury_factor": 1.0, "depreciation": "fast"},
    "Toyota": {"base": 28000, "luxury_factor": 1.0, "depreciation": "very_slow"},
    "Honda": {"base": 27000, "luxury_factor": 1.0, "depreciation": "very_slow"},
    "Nissan": {"base": 26000, "luxury_factor": 1.0, "depreciation": "moderate"},
    "Dodge": {"base": 31000, "luxury_factor": 1.1, "depreciation": "fast"},
    "Jeep": {"base": 35000, "luxury_factor": 1.1, "depreciation": "moderate"},
    "Subaru": {"base": 29000, "luxury_factor": 1.0, "depreciation": "slow"},
    "Mazda": {"base": 27000, "luxury_factor": 1.0, "depreciation": "moderate"},
    "Volkswagen": {"base": 28000, "luxury_factor": 1.2, "depreciation": "moderate"},
    "Hyundai": {"base": 24000, "luxury_factor": 1.0, "depreciation": "fast"},
    "Kia": {"base": 24000, "luxury_factor": 1.0, "depreciation": "fast"},
    "Genesis": {"base": 48000, "luxury_factor": 1.6, "depreciation": "moderate"},
    "Acura": {"base": 38000, "luxury_factor": 1.4, "depreciation": "slow"},
    "Infiniti": {"base": 42000, "luxury_factor": 1.5, "depreciation": "moderate"},
    "Cadillac": {"base": 47000, "luxury_factor": 1.6, "depreciation": "fast"},
    "Lincoln": {"base": 45000, "luxury_factor": 1.5, "depreciation": "fast"},
    "Ram": {"base": 38000, "luxury_factor": 1.1, "depreciation": "moderate"},
    "GMC": {"base": 42000, "luxury_factor": 1.2, "depreciation": "moderate"},
}

DEPRECIATION_RATES = {
    "very_slow": [0.15, 0.08, 0.07, 0.06, 0.05, 0.04, 0.04, 0.03, 0.03, 0.02],
    "slow": [0.18, 0.10, 0.08, 0.07, 0.06, 0.05, 0.04, 0.04, 0.03, 0.03],
    "moderate": [0.20, 0.12, 0.10, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03, 0.03],
    "fast": [0.25, 0.15, 0.12, 0.10, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03],
}

PERFORMANCE_MODELS = {
    "M": 1.8, "M3": 1.9, "M4": 2.0, "M5": 2.2, "M8": 2.5,
    "AMG": 2.0, "S": 1.4, "RS": 1.9, "R8": 3.0,
    "GT": 1.7, "GTI": 1.3, "GTS": 1.8, "GT-R": 2.5,
    "TURBO": 1.5, "S-LINE": 1.2, "TYPE R": 1.6,
    "STI": 1.5, "WRX": 1.3, "TRD": 1.3, "RAPTOR": 1.6,
    "HELLCAT": 2.2, "SCAT PACK": 1.5, "SRT": 1.6,
    "DENALI": 1.3, "PLATINUM": 1.2, "LIMITED": 1.15,
}

DAMAGE_TYPE_COSTS = {
    "bumper": 0.08,
    "fender": 0.12,
    "door": 0.15,
    "hood": 0.10,
    "trunk": 0.10,
    "windshield": 0.05,
    "headlight": 0.03,
    "taillight": 0.02,
    "mirror": 0.02,
    "wheel": 0.05,
    "suspension": 0.20,
    "frame": 0.50,
    "engine": 0.40,
    "transmission": 0.35,
    "airbag": 0.15,
    "electrical": 0.12,
    "paint": 0.08,
}

REGIONAL_MULTIPLIERS = {
    "CA": 1.25,
    "NY": 1.20,
    "HI": 1.30,
    "MA": 1.15,
    "WA": 1.12,
    "IL": 1.08,
    "FL": 1.05,
    "TX": 1.00,
    "OH": 0.95,
    "IN": 0.92,
    "SC": 0.90,
    "AL": 0.88,
    "MS": 0.85,
}


def calculate_vehicle_value(make: str, model: str, year: int) -> Tuple[float, Dict[str, Any]]:
    current_year = 2024
    age = max(0, current_year - year)

    vehicle_data = VEHICLE_MSRP_2024.get(make, {"base": 28000, "luxury_factor": 1.0, "depreciation": "moderate"})
    base_msrp = vehicle_data["base"]
    luxury_factor = vehicle_data["luxury_factor"]
    depreciation_type = vehicle_data["depreciation"]

    starting_value = base_msrp * luxury_factor

    performance_multiplier = 1.0
    model_upper = model.upper() if model else ""
    for perf_keyword, multiplier in PERFORMANCE_MODELS.items():
        if perf_keyword in model_upper:
            performance_multiplier = max(performance_multiplier, multiplier)
            break

    starting_value *= performance_multiplier

    depreciation_schedule = DEPRECIATION_RATES.get(depreciation_type, DEPRECIATION_RATES["moderate"])
    current_value = starting_value

    for year_index in range(min(age, len(depreciation_schedule))):
        depreciation_rate = depreciation_schedule[year_index]
        current_value *= (1 - depreciation_rate)

    if age > len(depreciation_schedule):
        remaining_years = age - len(depreciation_schedule)
        current_value *= (1 - 0.02) ** remaining_years

    current_value = max(current_value, 1500)

    metadata = {
        "starting_msrp": starting_value,
        "age": age,
        "depreciation_type": depreciation_type,
        "performance_multiplier": performance_multiplier,
        "estimated_current_value": current_value
    }

    return current_value, metadata


def estimate_repair_cost_by_severity(
    vehicle_value: float,
    severity: str,
    collision_type: str = None
) -> Tuple[float, str]:

    severity_upper = severity.upper() if severity else "MINOR DAMAGE"

    if "TOTAL" in severity_upper:
        return vehicle_value * 0.88, "Total loss: estimated at 88% of vehicle value"

    elif "MAJOR" in severity_upper:
        base_pct = 0.45
        if collision_type:
            if "FRONT" in collision_type.upper():
                base_pct = 0.50
            elif "REAR" in collision_type.upper():
                base_pct = 0.40
            elif "SIDE" in collision_type.upper():
                base_pct = 0.42
        return vehicle_value * base_pct, f"Major damage: {int(base_pct*100)}% of vehicle value"

    elif "MINOR" in severity_upper:
        base_pct = 0.18
        if collision_type and "REAR" in collision_type.upper():
            base_pct = 0.15
        return vehicle_value * base_pct, f"Minor damage: {int(base_pct*100)}% of vehicle value"

    elif "TRIVIAL" in severity_upper:
        return vehicle_value * 0.05, "Trivial damage: 5% of vehicle value"

    else:
        return vehicle_value * 0.20, "Estimated damage: 20% of vehicle value"


def apply_regional_adjustment(cost: float, state: str) -> Tuple[float, str]:
    multiplier = REGIONAL_MULTIPLIERS.get(state, 1.0)
    adjusted_cost = cost * multiplier

    if multiplier != 1.0:
        pct_change = int((multiplier - 1.0) * 100)
        direction = "higher" if pct_change > 0 else "lower"
        return adjusted_cost, f"Regional adjustment: {abs(pct_change)}% {direction} for {state}"

    return adjusted_cost, ""
