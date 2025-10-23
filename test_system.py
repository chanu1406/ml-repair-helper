#!/usr/bin/env python3
"""
Test script to verify the entire vehicle valuation system

This script tests:
1. NHTSA API integration
2. Database operations
3. Valuation service
4. End-to-end prediction with VIN
"""

import sys
from backend.app.nhtsa_service import decode_vin
from backend.app.valuation_service import get_vehicle_value
from backend.app.database.session import init_db
from backend.app.business_rules import apply_business_rules


def test_nhtsa_api():
    """Test NHTSA VIN decoding"""
    print("\n" + "=" * 60)
    print("TEST 1: NHTSA VIN Decoding")
    print("=" * 60)

    # Example VIN (2019 Toyota Camry)
    test_vin = "4T1B11HK5KU211111"

    try:
        result = decode_vin(test_vin)
        print(f"✓ Successfully decoded VIN: {test_vin}")
        print(f"  Make: {result.get('make')}")
        print(f"  Model: {result.get('model')}")
        print(f"  Year: {result.get('year')}")
        print(f"  Trim: {result.get('trim')}")
        print(f"  Body Type: {result.get('body_type')}")
        return True
    except Exception as e:
        print(f"✗ NHTSA test failed: {e}")
        return False


def test_database():
    """Test database initialization"""
    print("\n" + "=" * 60)
    print("TEST 2: Database Initialization")
    print("=" * 60)

    try:
        init_db()
        print("✓ Database initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False


def test_valuation_service():
    """Test valuation service"""
    print("\n" + "=" * 60)
    print("TEST 3: Valuation Service")
    print("=" * 60)

    try:
        # Test with make/model/year (will use fallback initially)
        value, metadata = get_vehicle_value(
            make="Toyota",
            model="Camry",
            year=2020,
            mileage=50000,
            state="CA"
        )

        print(f"✓ Valuation service working")
        print(f"  Estimated value: ${value:,.0f}")
        print(f"  Data source: {metadata.get('data_source')}")
        print(f"  Confidence: {metadata.get('confidence')}")
        return True
    except Exception as e:
        print(f"✗ Valuation test failed: {e}")
        return False


def test_business_rules():
    """Test end-to-end business rules with new system"""
    print("\n" + "=" * 60)
    print("TEST 4: Business Rules Integration")
    print("=" * 60)

    features = {
        "auto_make": "Toyota",
        "auto_model": "Camry",
        "auto_year": 2020,
        "auto_mileage": 50000,
        "incident_severity": "Major Damage",
        "collision_type": "Front Collision",
        "policy_state": "CA",
        "bodily_injuries": 1,
        "vin": "4T1B11HK5KU211111"  # Optional
    }

    try:
        result = apply_business_rules(
            base_prediction=15000,
            features=features
        )

        print("✓ Business rules working")
        print(f"  Predicted cost: ${result['predicted_cost']:,.0f}")
        print(f"  Vehicle value: ${result['estimated_vehicle_value']:,.0f}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Reasoning: {result['reasoning'][0]}")

        if result.get('valuation_details'):
            print(f"  Data source: {result['valuation_details'].get('data_source', 'N/A')}")

        return True
    except Exception as e:
        print(f"✗ Business rules test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("VEHICLE VALUATION SYSTEM - TEST SUITE")
    print("=" * 60)

    tests = [
        ("NHTSA API", test_nhtsa_api),
        ("Database", test_database),
        ("Valuation Service", test_valuation_service),
        ("Business Rules", test_business_rules)
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n✗ {name} test crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status:8} {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
