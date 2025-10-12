"""Test script for the RepairHelper API."""

import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

# Sample data (first row from dataset)
sample_features = {
    "months_as_customer": 328,
    "age": 48,
    "policy_number": 521585,
    "policy_bind_date": "2014-10-17",
    "policy_state": "OH",
    "policy_csl": "250/500",
    "policy_deductable": 1000,
    "policy_annual_premium": 1406.91,
    "umbrella_limit": 0,
    "insured_zip": 466132,
    "insured_sex": "MALE",
    "insured_education_level": "MD",
    "insured_occupation": "craft-repair",
    "insured_hobbies": "sleeping",
    "insured_relationship": "husband",
    "capital-gains": 53300,
    "capital-loss": 0,
    "incident_date": "2015-01-25",
    "incident_type": "Single Vehicle Collision",
    "collision_type": "Side Collision",
    "incident_severity": "Major Damage",
    "authorities_contacted": "Police",
    "incident_state": "SC",
    "incident_city": "Columbus",
    "incident_location": "9935 4th Drive",
    "incident_hour_of_the_day": 5,
    "number_of_vehicles_involved": 1,
    "property_damage": "YES",
    "bodily_injuries": 1,
    "witnesses": 2,
    "police_report_available": "YES",
    "injury_claim": 6510,
    "property_claim": 13020,
    "vehicle_claim": 52080,
    "auto_make": "Saab",
    "auto_model": "92x",
    "auto_year": 2004,
    "fraud_reported": "Y"
}


def test_health():
    """Test the health endpoint."""
    print("=" * 50)
    print("Testing /health endpoint")
    print("=" * 50)
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_model_info():
    """Test the model-info endpoint."""
    print("=" * 50)
    print("Testing /model-info endpoint")
    print("=" * 50)
    response = requests.get(f"{BASE_URL}/model-info")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_predict():
    """Test the predict endpoint."""
    print("=" * 50)
    print("Testing /predict endpoint")
    print("=" * 50)

    payload = {"features": sample_features}
    response = requests.post(f"{BASE_URL}/predict", json=payload)

    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        predicted_cost = response.json()["predicted_cost"]
        actual_cost = 71610  # From the dataset
        print(f"\nActual cost: ${actual_cost:,.2f}")
        print(f"Predicted cost: ${predicted_cost:,.2f}")
        print(f"Error: ${abs(actual_cost - predicted_cost):,.2f}")
    print()


if __name__ == "__main__":
    print("\n🚀 RepairHelper API Test Suite\n")

    test_health()
    test_model_info()
    test_predict()

    print("=" * 50)
    print("✅ All tests completed!")
    print("=" * 50)
