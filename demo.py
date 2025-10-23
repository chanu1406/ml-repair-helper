#!/usr/bin/env python3
"""
Interactive Demo - RepairHelper Improved Model

This script demonstrates the improved model's capabilities with
an interactive menu.
"""

from ml.model_wrapper import ImprovedModelWrapper
import json

def print_banner():
    print("\n" + "="*60)
    print("  RepairHelper - Improved ML Model Demo")
    print("="*60)

def print_menu():
    print("\nWhat would you like to do?")
    print("  1. Quick demo (3 example predictions)")
    print("  2. Compare damage severities")
    print("  3. Compare vehicle types")
    print("  4. Compare regional differences")
    print("  5. Custom prediction (enter your own values)")
    print("  6. View model performance")
    print("  7. View business rules")
    print("  0. Exit")
    print()

def quick_demo(wrapper):
    """Demo with 3 example scenarios"""
    print("\n" + "="*60)
    print("QUICK DEMO - 3 Example Scenarios")
    print("="*60)

    scenarios = [
        {
            "name": "Minor Fender Bender",
            "claim": {
                "auto_make": "Honda",
                "auto_model": "Civic",
                "auto_year": 2020,
                "incident_severity": "Minor Damage",
                "collision_type": "Rear Collision",
                "incident_state": "OH",
                "bodily_injuries": 0,
                "months_as_customer": 24,
                "age": 28,
                "policy_deductable": 500,
                "policy_annual_premium": 1000
            }
        },
        {
            "name": "Major Collision",
            "claim": {
                "auto_make": "Toyota",
                "auto_model": "Camry",
                "auto_year": 2018,
                "incident_severity": "Major Damage",
                "collision_type": "Front Collision",
                "incident_state": "NY",
                "bodily_injuries": 1,
                "months_as_customer": 36,
                "age": 35,
                "policy_deductable": 1000,
                "policy_annual_premium": 1200
            }
        },
        {
            "name": "Total Loss (Luxury Vehicle)",
            "claim": {
                "auto_make": "BMW",
                "auto_model": "3 Series",
                "auto_year": 2019,
                "incident_severity": "Total Loss",
                "collision_type": "Side Collision",
                "incident_state": "SC",
                "bodily_injuries": 2,
                "months_as_customer": 48,
                "age": 42,
                "policy_deductable": 1000,
                "policy_annual_premium": 2500
            }
        }
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print("-" * 60)
        claim = scenario['claim']
        print(f"   Vehicle: {claim['auto_year']} {claim['auto_make']} {claim['auto_model']}")
        print(f"   Severity: {claim['incident_severity']}")
        print(f"   State: {claim['incident_state']}")
        print(f"   Injuries: {claim['bodily_injuries']}")

        result = wrapper.predict(claim)
        print(f"\n   💰 Predicted Cost: ${result['predicted_cost']:,.2f}")

        if 'severity_ratio' in result:
            print(f"   📊 Severity Ratio: {result['severity_ratio']:.1%} of vehicle value")

def compare_severities(wrapper):
    """Compare different damage severities"""
    print("\n" + "="*60)
    print("COMPARING DAMAGE SEVERITIES")
    print("="*60)

    base_claim = {
        "auto_make": "Toyota",
        "auto_model": "Camry",
        "auto_year": 2020,
        "incident_state": "OH",
        "collision_type": "Front Collision",
        "bodily_injuries": 0,
        "months_as_customer": 36,
        "age": 35,
        "policy_deductable": 1000,
        "policy_annual_premium": 1200
    }

    print(f"\nVehicle: {base_claim['auto_year']} {base_claim['auto_make']} {base_claim['auto_model']}")
    print(f"Location: {base_claim['incident_state']}")
    print(f"No injuries\n")

    severities = ["Trivial Damage", "Minor Damage", "Major Damage", "Total Loss"]

    print(f"{'Severity':<20} {'Predicted Cost':>20}")
    print("-" * 42)

    for severity in severities:
        claim = base_claim.copy()
        claim['incident_severity'] = severity
        result = wrapper.predict(claim)
        print(f"{severity:<20} ${result['predicted_cost']:>19,.2f}")

def compare_vehicles(wrapper):
    """Compare different vehicle types"""
    print("\n" + "="*60)
    print("COMPARING VEHICLE TYPES")
    print("="*60)

    base_claim = {
        "auto_year": 2020,
        "incident_severity": "Major Damage",
        "collision_type": "Front Collision",
        "incident_state": "OH",
        "bodily_injuries": 0,
        "months_as_customer": 36,
        "age": 35,
        "policy_deductable": 1000,
        "policy_annual_premium": 1500
    }

    vehicles = [
        ("Honda", "Civic", "Economy"),
        ("Toyota", "Camry", "Mid-size"),
        ("Ford", "F-150", "Truck"),
        ("BMW", "3 Series", "Luxury"),
        ("Mercedes", "C-Class", "Luxury")
    ]

    print(f"\nAll vehicles: 2020 model year, Major Damage")
    print(f"Location: OH, No injuries\n")

    print(f"{'Vehicle':<30} {'Type':<15} {'Predicted Cost':>15}")
    print("-" * 62)

    for make, model, vtype in vehicles:
        claim = base_claim.copy()
        claim['auto_make'] = make
        claim['auto_model'] = model
        result = wrapper.predict(claim)
        vehicle_name = f"{make} {model}"
        print(f"{vehicle_name:<30} {vtype:<15} ${result['predicted_cost']:>14,.2f}")

def compare_regions(wrapper):
    """Compare regional differences"""
    print("\n" + "="*60)
    print("COMPARING REGIONAL COSTS")
    print("="*60)

    base_claim = {
        "auto_make": "Toyota",
        "auto_model": "Camry",
        "auto_year": 2020,
        "incident_severity": "Major Damage",
        "collision_type": "Front Collision",
        "bodily_injuries": 0,
        "months_as_customer": 36,
        "age": 35,
        "policy_deductable": 1000,
        "policy_annual_premium": 1200
    }

    states = ["NY", "SC", "OH", "PA", "NC", "VA", "WV"]

    print(f"\nVehicle: 2020 Toyota Camry, Major Damage, No injuries\n")

    print(f"{'State':<10} {'Predicted Cost':>20} {'Regional Multiplier':>22}")
    print("-" * 54)

    for state in states:
        claim = base_claim.copy()
        claim['incident_state'] = state
        claim['policy_state'] = state
        result = wrapper.predict(claim)
        mult = result.get('regional_multiplier', 1.0)
        print(f"{state:<10} ${result['predicted_cost']:>19,.2f}   {mult:>19.2f}x")

def custom_prediction(wrapper):
    """Get user input for custom prediction"""
    print("\n" + "="*60)
    print("CUSTOM PREDICTION")
    print("="*60)
    print("\nEnter claim details (press Enter for defaults):\n")

    # Get user input
    make = input("Vehicle Make [Toyota]: ").strip() or "Toyota"
    model = input("Vehicle Model [Camry]: ").strip() or "Camry"
    year = input("Vehicle Year [2020]: ").strip() or "2020"

    print("\nSeverity: Trivial Damage, Minor Damage, Major Damage, Total Loss")
    severity = input("Incident Severity [Major Damage]: ").strip() or "Major Damage"

    print("\nCollision: Front Collision, Rear Collision, Side Collision")
    collision = input("Collision Type [Front Collision]: ").strip() or "Front Collision"

    state = input("State (2-letter code) [OH]: ").strip().upper() or "OH"
    injuries = input("Number of Injuries [0]: ").strip() or "0"

    # Build claim
    claim = {
        "auto_make": make,
        "auto_model": model,
        "auto_year": int(year),
        "incident_severity": severity,
        "collision_type": collision,
        "incident_state": state,
        "policy_state": state,
        "bodily_injuries": int(injuries),
        "months_as_customer": 36,
        "age": 35,
        "policy_deductable": 1000,
        "policy_annual_premium": 1200
    }

    # Predict
    print("\n" + "-" * 60)
    result = wrapper.predict(claim)

    print(f"\n🎯 PREDICTION RESULT:")
    print(f"   Vehicle: {year} {make} {model}")
    print(f"   Severity: {severity}")
    print(f"   Location: {state}")
    print(f"   Injuries: {injuries}")
    print(f"\n   💰 Predicted Cost: ${result['predicted_cost']:,.2f}")

    if 'severity_ratio' in result:
        print(f"   📊 Severity Ratio: {result['severity_ratio']:.1%}")
    if 'regional_multiplier' in result:
        print(f"   📍 Regional Multiplier: {result['regional_multiplier']:.2f}x")

def view_performance(wrapper):
    """Display model performance metrics"""
    print("\n" + "="*60)
    print("MODEL PERFORMANCE METRICS")
    print("="*60)

    meta = wrapper.metadata

    print(f"\n📊 Improved Model Statistics:")
    print(f"   • Dataset: {meta['dataset']}")
    print(f"   • Features: {meta['features_count']}")
    print(f"   • Training samples: {meta['training_samples']:,}")
    print(f"   • Validation samples: {meta['validation_samples']:,}")

    print(f"\n🎯 Accuracy Metrics:")
    print(f"   • MAE (Mean Absolute Error):     ${meta['mae']:,.2f}")
    print(f"   • RMSE (Root Mean Squared Error): ${meta['rmse']:,.2f}")
    print(f"   • R² Score:                       {meta['r2']:.4f}")
    print(f"   • Median Absolute Error:          ${meta['median_ae']:,.2f}")
    print(f"   • MAPE (Mean Abs % Error):        {meta['mape']:.2f}%")

    print(f"\n✨ What This Means:")
    print(f"   • Half of predictions are within ${meta['median_ae']:,.0f}")
    print(f"   • On average, predictions are off by ~{meta['mape']:.1f}%")
    print(f"   • Model explains {meta['r2']*100:.2f}% of variance in claims")

def view_business_rules(wrapper):
    """Display data-driven business rules"""
    print("\n" + "="*60)
    print("DATA-DRIVEN BUSINESS RULES")
    print("="*60)

    rules = wrapper.business_rules

    print("\n📍 Regional Multipliers:")
    print("   (How much more/less expensive by state)")
    print()
    regional = sorted(rules['regional_multipliers'].items(), key=lambda x: x[1], reverse=True)
    for state, mult in regional:
        pct = (mult - 1) * 100
        print(f"   {state}: {mult:.2f}x ({pct:+.0f}%)")

    print("\n📊 Severity Ratios:")
    print("   (Damage cost as % of vehicle value)")
    print()
    severity = sorted(rules['severity_ratios'].items(), key=lambda x: x[1])
    for sev, ratio in severity:
        print(f"   {sev:<20} {ratio:>6.1%}")

    print("\n🚗 Collision Type Multipliers:")
    collision = sorted(rules['collision_type_multipliers'].items(), key=lambda x: x[1], reverse=True)
    for col_type, mult in collision:
        pct = (mult - 1) * 100
        print(f"   {col_type:<20} {mult:.2f}x ({pct:+.0f}%)")

def main():
    """Main interactive loop"""
    print_banner()

    # Load model
    print("\nLoading improved model...")
    wrapper = ImprovedModelWrapper()
    print()

    while True:
        print_menu()
        choice = input("Enter your choice (0-7): ").strip()

        if choice == "0":
            print("\nThank you for using RepairHelper! 👋\n")
            break
        elif choice == "1":
            quick_demo(wrapper)
        elif choice == "2":
            compare_severities(wrapper)
        elif choice == "3":
            compare_vehicles(wrapper)
        elif choice == "4":
            compare_regions(wrapper)
        elif choice == "5":
            custom_prediction(wrapper)
        elif choice == "6":
            view_performance(wrapper)
        elif choice == "7":
            view_business_rules(wrapper)
        else:
            print("\n❌ Invalid choice. Please enter 0-7.")

        input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting... 👋\n")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
