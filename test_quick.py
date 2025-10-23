#!/usr/bin/env python3
"""
Quick interactive test script for the vehicle valuation system
"""

print("\n" + "="*60)
print("VEHICLE VALUATION SYSTEM - QUICK TEST")
print("="*60)

# Test 1: NHTSA API
print("\n[1/4] Testing NHTSA API...")
try:
    from backend.app.nhtsa_service import decode_vin

    # Real VIN example - 2019 Toyota Camry
    test_vin = "4T1B11HK5KU211111"
    print(f"   Decoding VIN: {test_vin}")

    result = decode_vin(test_vin)

    print(f"   ✓ SUCCESS!")
    print(f"   Make: {result.get('make')}")
    print(f"   Model: {result.get('model')}")
    print(f"   Year: {result.get('year')}")
    print(f"   Body Type: {result.get('body_type')}")

except Exception as e:
    print(f"   ✗ FAILED: {e}")

# Test 2: Database
print("\n[2/4] Testing Database...")
try:
    from backend.app.database.session import init_db

    init_db()
    print("   ✓ Database initialized successfully")
    print("   Database file: vehicle_data.db")

except Exception as e:
    print(f"   ✗ FAILED: {e}")

# Test 3: Valuation Service (Fallback Mode)
print("\n[3/4] Testing Valuation Service...")
try:
    from backend.app.valuation_service import get_vehicle_value

    print("   Getting value for 2020 Toyota Camry...")
    value, metadata = get_vehicle_value(
        make="Toyota",
        model="Camry",
        year=2020,
        mileage=50000,
        state="CA"
    )

    print(f"   ✓ SUCCESS!")
    print(f"   Estimated Value: ${value:,.0f}")
    print(f"   Data Source: {metadata.get('data_source')}")
    print(f"   Confidence: {metadata.get('confidence')}")

    if metadata.get('data_source') == 'fallback_model':
        print("   Note: Using fallback model (no market data yet)")
        print("   Run scrapers to get real market data!")

except Exception as e:
    print(f"   ✗ FAILED: {e}")

# Test 4: Complete Business Rules Flow
print("\n[4/4] Testing Complete Prediction Flow...")
try:
    from backend.app.business_rules import apply_business_rules

    features = {
        "auto_make": "Toyota",
        "auto_model": "Camry",
        "auto_year": 2020,
        "auto_mileage": 50000,
        "incident_severity": "Major Damage",
        "collision_type": "Front Collision",
        "policy_state": "CA",
        "bodily_injuries": 1
    }

    print("   Predicting repair cost for:")
    print(f"   - Vehicle: 2020 Toyota Camry")
    print(f"   - Mileage: 50,000 miles")
    print(f"   - Damage: Major (Front Collision)")
    print(f"   - Location: California")

    result = apply_business_rules(
        base_prediction=15000,
        features=features
    )

    print(f"\n   ✓ SUCCESS!")
    print(f"   Predicted Repair Cost: ${result['predicted_cost']:,.0f}")
    print(f"   Estimated Vehicle Value: ${result['estimated_vehicle_value']:,.0f}")
    print(f"   Confidence: {result['confidence']}")
    print(f"   Reasoning: {result['reasoning'][0]}")

except Exception as e:
    print(f"   ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "="*60)
print("TEST COMPLETE!")
print("="*60)
print("\nNext Steps:")
print("1. Run 'python run_scraper.py --help' to see scraper options")
print("2. Scrape some data: python run_scraper.py --make Toyota --model Camry --max-results 20")
print("3. Start API: cd backend && uvicorn app.main:app --reload")
print("4. Visit http://localhost:8000/docs for API documentation")
print("="*60 + "\n")
