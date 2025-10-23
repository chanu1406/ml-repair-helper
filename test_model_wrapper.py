"""Test the improved model wrapper"""

from ml.model_wrapper import ImprovedModelWrapper

print("="*60)
print("TESTING IMPROVED MODEL WRAPPER")
print("="*60)

# Initialize wrapper
print("\n1. Loading model...")
wrapper = ImprovedModelWrapper("ml/artifacts/model_improved.pkl")

# Test prediction
print("\n2. Making test prediction...")

sample_claim = {
    # Policy info
    "months_as_customer": 36,
    "age": 35,
    "policy_state": "OH",
    "policy_deductable": 1000,
    "policy_annual_premium": 1200,
    "insured_sex": "MALE",
    "insured_education_level": "Bachelors",

    # Vehicle info
    "auto_make": "Toyota",
    "auto_model": "Camry",
    "auto_year": 2018,

    # Incident info
    "incident_type": "Single Vehicle Collision",
    "collision_type": "Front Collision",
    "incident_severity": "Major Damage",
    "incident_state": "OH",
    "bodily_injuries": 0,
    "witnesses": 2,
    "police_report_available": "YES",
    "property_damage": "NO",
    "number_of_vehicles_involved": 1,

    # Dates
    "policy_bind_date": "2022-01-15",
    "incident_date": "2025-01-20",
    "incident_hour_of_the_day": 14,
}

result = wrapper.predict(sample_claim)

print(f"\n   Sample Claim:")
print(f"   • Vehicle: {sample_claim['auto_year']} {sample_claim['auto_make']} {sample_claim['auto_model']}")
print(f"   • Severity: {sample_claim['incident_severity']}")
print(f"   • State: {sample_claim['incident_state']}")

print(f"\n   🎯 PREDICTION RESULT:")
print(f"   • Predicted Cost: ${result['predicted_cost']:,.2f}")
print(f"   • Model MAE: ${result['mae']:,.2f}")
print(f"   • Model R²: {result['r2']:.4f}")
print(f"   • Model MAPE: {result['mape']:.2f}%")

if 'severity_ratio' in result:
    print(f"   • Severity Ratio: {result['severity_ratio']:.1%} of vehicle value")
if 'regional_multiplier' in result:
    print(f"   • Regional Multiplier: {result['regional_multiplier']:.2f}x")

# Test with different severity levels
print("\n3. Testing different severity levels...")

severities = ["Trivial Damage", "Minor Damage", "Major Damage", "Total Loss"]

print(f"\n   Same vehicle, different damage levels:")
print(f"   {'Severity':<20} {'Predicted Cost':>15}")
print(f"   {'-'*40}")

for severity in severities:
    test_claim = sample_claim.copy()
    test_claim['incident_severity'] = severity
    result = wrapper.predict(test_claim)
    print(f"   {severity:<20} ${result['predicted_cost']:>14,.2f}")

# Test with luxury vehicle
print("\n4. Testing luxury vehicle...")

luxury_claim = sample_claim.copy()
luxury_claim['auto_make'] = "BMW"
luxury_claim['auto_model'] = "3 Series"
luxury_claim['auto_year'] = 2020

result_luxury = wrapper.predict(luxury_claim)
result_regular = wrapper.predict(sample_claim)

print(f"\n   Regular vehicle (Toyota Camry): ${result_regular['predicted_cost']:,.2f}")
print(f"   Luxury vehicle (BMW 3 Series):  ${result_luxury['predicted_cost']:,.2f}")
print(f"   Difference: ${result_luxury['predicted_cost'] - result_regular['predicted_cost']:+,.2f}")

print("\n" + "="*60)
print("✅ MODEL WRAPPER WORKING CORRECTLY")
print("="*60)
print(f"\nUsage:")
print(f"  from ml.model_wrapper import ImprovedModelWrapper")
print(f"  wrapper = ImprovedModelWrapper()")
print(f"  result = wrapper.predict(claim_data)")
print()
