import requests
import json

API_URL = "http://localhost:8000"

test_scenarios = [
    {
        "name": "2020 BMW M4 - Total Loss (California - High Cost State)",
        "auto_make": "BMW",
        "auto_model": "M4",
        "auto_year": 2020,
        "incident_severity": "Total Loss",
        "collision_type": "Front Collision",
        "policy_state": "CA",
        "bodily_injuries": 0,
        "expected": "~$62k (88% of ~$70k vehicle value in high-cost CA)"
    },
    {
        "name": "2022 Tesla Model 3 - Major Front Collision (Texas)",
        "auto_make": "Tesla",
        "auto_model": "Model 3",
        "auto_year": 2022,
        "incident_severity": "Major Damage",
        "collision_type": "Front Collision",
        "policy_state": "TX",
        "bodily_injuries": 1,
        "expected": "~$23k (50% vehicle value + $5k injury)"
    },
    {
        "name": "2015 Toyota Camry - Minor Rear Collision (Ohio)",
        "auto_make": "Toyota",
        "auto_model": "Camry",
        "auto_year": 2015,
        "incident_severity": "Minor Damage",
        "collision_type": "Rear Collision",
        "policy_state": "OH",
        "bodily_injuries": 0,
        "expected": "~$2k (15% of vehicle value, lower cost state)"
    },
    {
        "name": "2018 Honda Civic - Trivial Damage (New York - High Cost)",
        "auto_make": "Honda",
        "auto_model": "Civic",
        "auto_year": 2018,
        "incident_severity": "Trivial Damage",
        "collision_type": "Side Collision",
        "policy_state": "NY",
        "bodily_injuries": 0,
        "expected": "~$1k (5% of vehicle value with NY multiplier)"
    },
    {
        "name": "2023 Porsche 911 GT3 - Major Damage (California)",
        "auto_make": "Porsche",
        "auto_model": "911 GT3",
        "auto_year": 2023,
        "incident_severity": "Major Damage",
        "collision_type": "Side Collision",
        "policy_state": "CA",
        "bodily_injuries": 2,
        "expected": "~$90k (high-value performance car + 2 injuries)"
    },
]


def build_features(scenario):
    return {
        "months_as_customer": 24,
        "age": 35,
        "policy_number": 0,
        "policy_bind_date": "2020-01-01",
        "policy_state": scenario["policy_state"],
        "policy_csl": "250/500",
        "policy_deductable": 1000,
        "policy_annual_premium": 2000.0,
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
        "collision_type": scenario["collision_type"],
        "incident_severity": scenario["incident_severity"],
        "authorities_contacted": "Police",
        "incident_state": scenario["policy_state"],
        "incident_city": "Test City",
        "incident_location": "Main St",
        "incident_hour_of_the_day": 14,
        "number_of_vehicles_involved": 1,
        "property_damage": "NO",
        "bodily_injuries": scenario["bodily_injuries"],
        "witnesses": 1,
        "police_report_available": "YES",
        "injury_claim": 0,
        "property_claim": 0,
        "vehicle_claim": 0,
        "auto_make": scenario["auto_make"],
        "auto_model": scenario["auto_model"],
        "auto_year": scenario["auto_year"],
        "fraud_reported": "N"
    }


print("\n" + "="*80)
print("🧪 ENHANCED PREDICTION SYSTEM TEST SUITE")
print("="*80)

for i, scenario in enumerate(test_scenarios, 1):
    print(f"\n{'='*80}")
    print(f"TEST {i}/{len(test_scenarios)}: {scenario['name']}")
    print(f"{'='*80}")
    print(f"Expected: {scenario['expected']}")
    print(f"{'-'*80}")

    features = build_features(scenario)

    try:
        response = requests.post(
            f"{API_URL}/predict",
            json={"features": features},
            timeout=5
        )

        if response.status_code == 200:
            result = response.json()

            print(f"✅ SUCCESS")
            print(f"\n💰 Predicted Repair Cost: ${result['predicted_cost']:,.2f}")
            print(f"🚗 Vehicle Value:         ${result['estimated_vehicle_value']:,.0f}")
            print(f"📊 Confidence:            {result['confidence']}")

            if result.get('valuation_details'):
                details = result['valuation_details']
                print(f"\n📋 Valuation Details:")
                print(f"   • Vehicle Age: {details.get('age', 'N/A')} years")
                print(f"   • Depreciation Type: {details.get('depreciation_type', 'N/A')}")
                if details.get('performance_multiplier', 1.0) > 1.0:
                    print(f"   • Performance Multiplier: {details['performance_multiplier']}x")

            if result.get('reasoning'):
                print(f"\n📝 Reasoning:")
                for reason in result['reasoning']:
                    print(f"   • {reason}")

        else:
            print(f"❌ FAILED - Status: {response.status_code}")
            print(f"Error: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ CONNECTION ERROR: {e}")

    print(f"{'='*80}\n")

print("="*80)
print("✅ TEST SUITE COMPLETE")
print("="*80 + "\n")
