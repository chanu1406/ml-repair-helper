import requests
import json

API_URL = "http://localhost:8000"

test_cases = [
    {
        "name": "2020 BMW M4 - Total Loss",
        "features": {
            "months_as_customer": 24,
            "age": 35,
            "policy_number": 0,
            "policy_bind_date": "2020-01-01",
            "policy_state": "CA",
            "policy_csl": "250/500",
            "policy_deductable": 1000,
            "policy_annual_premium": 2500.0,
            "umbrella_limit": 0,
            "insured_zip": 90210,
            "insured_sex": "MALE",
            "insured_education_level": "College",
            "insured_occupation": "exec-managerial",
            "insured_hobbies": "golf",
            "insured_relationship": "husband",
            "capital-gains": 0,
            "capital-loss": 0,
            "incident_date": "2024-10-01",
            "incident_type": "Single Vehicle Collision",
            "collision_type": "Front Collision",
            "incident_severity": "Total Loss",
            "authorities_contacted": "Police",
            "incident_state": "CA",
            "incident_city": "Los Angeles",
            "incident_location": "Main St",
            "incident_hour_of_the_day": 14,
            "number_of_vehicles_involved": 1,
            "property_damage": "NO",
            "bodily_injuries": 0,
            "witnesses": 1,
            "police_report_available": "YES",
            "injury_claim": 0,
            "property_claim": 0,
            "vehicle_claim": 0,
            "auto_make": "BMW",
            "auto_model": "M4",
            "auto_year": 2020,
            "fraud_reported": "N"
        }
    },
    {
        "name": "2010 Toyota Camry - Minor Damage",
        "features": {
            "months_as_customer": 60,
            "age": 45,
            "policy_number": 0,
            "policy_bind_date": "2015-01-01",
            "policy_state": "OH",
            "policy_csl": "250/500",
            "policy_deductable": 500,
            "policy_annual_premium": 1200.0,
            "umbrella_limit": 0,
            "insured_zip": 43215,
            "insured_sex": "FEMALE",
            "insured_education_level": "College",
            "insured_occupation": "sales",
            "insured_hobbies": "reading",
            "insured_relationship": "wife",
            "capital-gains": 0,
            "capital-loss": 0,
            "incident_date": "2024-09-15",
            "incident_type": "Multi-vehicle Collision",
            "collision_type": "Rear Collision",
            "incident_severity": "Minor Damage",
            "authorities_contacted": "None",
            "incident_state": "OH",
            "incident_city": "Columbus",
            "incident_location": "High St",
            "incident_hour_of_the_day": 17,
            "number_of_vehicles_involved": 2,
            "property_damage": "NO",
            "bodily_injuries": 0,
            "witnesses": 2,
            "police_report_available": "NO",
            "injury_claim": 0,
            "property_claim": 0,
            "vehicle_claim": 0,
            "auto_make": "Toyota",
            "auto_model": "Camry",
            "auto_year": 2010,
            "fraud_reported": "N"
        }
    }
]

print("🧪 Testing Enhanced Predictions\n")
print("=" * 70)

for test in test_cases:
    print(f"\n📋 Test Case: {test['name']}")
    print("-" * 70)

    response = requests.post(
        f"{API_URL}/predict",
        json={"features": test["features"]}
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Status: SUCCESS")
        print(f"\n💰 Predicted Repair Cost: ${result['predicted_cost']:,.2f}")
        print(f"🚗 Est. Vehicle Value:    ${result['estimated_vehicle_value']:,.0f}")
        print(f"📊 Confidence:            {result['confidence']}")

        if result.get('base_model_prediction'):
            print(f"🤖 Base Model Prediction: ${result['base_model_prediction']:,.2f}")

        if result.get('reasoning'):
            print(f"\n📝 Reasoning:")
            for reason in result['reasoning']:
                print(f"   • {reason}")
    else:
        print(f"❌ Status: FAILED")
        print(f"Error: {response.json()}")

    print("=" * 70)

print("\n✅ Testing Complete!")
