"""
Test script for the improved model

This verifies that the improved model can be loaded and used for predictions.
"""

import json
import joblib
import pandas as pd
from pathlib import Path

print("="*60)
print("TESTING IMPROVED MODEL")
print("="*60)

# Load improved model
model_path = Path("ml/artifacts/model_improved.pkl")
if not model_path.exists():
    print(f"❌ Model not found at {model_path}")
    exit(1)

print(f"\n1. Loading improved model from {model_path}...")
pipeline = joblib.load(model_path)
print("   ✓ Model loaded successfully")

# Load metadata
meta_path = Path("ml/artifacts/model_improved_metadata.json")
with open(meta_path, 'r') as f:
    metadata = json.load(f)

print(f"\n2. Model Metadata:")
print(f"   • Dataset: {metadata['dataset']}")
print(f"   • Target: {metadata['target']}")
print(f"   • Features: {metadata['features_count']}")
print(f"   • Training samples: {metadata['training_samples']}")
print(f"   • MAE: ${metadata['mae']:,.2f}")
print(f"   • R²: {metadata['r2']:.4f}")
print(f"   • MAPE: {metadata['mape']:.2f}%")

# Load business rules
rules_path = Path("ml/artifacts/business_rules.json")
with open(rules_path, 'r') as f:
    business_rules = json.load(f)

print(f"\n3. Data-Driven Business Rules:")
print(f"   • Regional multipliers: {len(business_rules['regional_multipliers'])} states")
print(f"   • Severity ratios: {len(business_rules['severity_ratios'])} levels")
print(f"   • Collision types: {len(business_rules['collision_type_multipliers'])} types")

# Create test prediction
print(f"\n4. Testing prediction with sample claim...")

# Sample claim data (typical moderate accident)
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

    # Dates (for feature engineering)
    "policy_bind_date": "2022-01-15",
    "incident_date": "2025-01-20",
    "incident_hour_of_the_day": 14,
}

# Convert to DataFrame
X_test = pd.DataFrame([sample_claim])

try:
    # Make prediction
    prediction = pipeline.predict(X_test)[0]

    print(f"   ✓ Prediction successful!")
    print(f"\n   Sample Claim Details:")
    print(f"   • Vehicle: {sample_claim['auto_year']} {sample_claim['auto_make']} {sample_claim['auto_model']}")
    print(f"   • Severity: {sample_claim['incident_severity']}")
    print(f"   • Collision: {sample_claim['collision_type']}")
    print(f"   • Injuries: {sample_claim['bodily_injuries']}")
    print(f"\n   🎯 PREDICTED COST: ${prediction:,.2f}")

    # Show business rule adjustment
    severity = sample_claim['incident_severity']
    if severity in business_rules['severity_ratios']:
        severity_ratio = business_rules['severity_ratios'][severity]
        print(f"\n   📊 Business Rule Applied:")
        print(f"   • {severity}: {severity_ratio:.1%} of vehicle value")

except Exception as e:
    print(f"   ❌ Prediction failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Compare with baseline
baseline_path = Path("ml/artifacts/model.pkl")
if baseline_path.exists():
    print(f"\n5. Comparing with baseline model...")
    baseline_pipeline = joblib.load(baseline_path)
    baseline_pred = baseline_pipeline.predict(X_test)[0]

    diff = prediction - baseline_pred
    diff_pct = (diff / baseline_pred) * 100

    print(f"   • Baseline prediction: ${baseline_pred:,.2f}")
    print(f"   • Improved prediction: ${prediction:,.2f}")
    print(f"   • Difference: ${diff:+,.2f} ({diff_pct:+.1f}%)")

print("\n" + "="*60)
print("✅ ALL TESTS PASSED - IMPROVED MODEL IS READY")
print("="*60)
print(f"\nTo use in production:")
print(f"1. Load model: joblib.load('ml/artifacts/model_improved.pkl')")
print(f"2. Load rules: json.load('ml/artifacts/business_rules.json')")
print(f"3. Make predictions with same feature engineering as training")
print()
