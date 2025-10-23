import streamlit as st
import requests
import json
from datetime import datetime


API_URL = "http://localhost:8000"


st.set_page_config(
    page_title="RepairHelper - Insurance Claim Estimator",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 RepairHelper")
st.markdown("**Accurate repair cost estimates for auto insurance claims**")


def get_model_info():
    try:
        response = requests.get(f"{API_URL}/model-info")
        if response.status_code == 200:
            return response.json()
    except:
        return None


def predict_cost(features):
    try:
        response = requests.post(
            f"{API_URL}/predict",
            json={"features": features}
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.json().get("detail", "Unknown error")}
    except Exception as e:
        return {"error": f"Could not connect to API: {str(e)}"}


# Sidebar - Model Info
st.sidebar.header("📊 Model Info")
model_info = get_model_info()
if model_info:
    st.sidebar.success("✅ Model Active")
    st.sidebar.metric("Accuracy (R²)", f"{model_info['metadata']['r2']:.3f}")
    st.sidebar.metric("Avg Error", f"${model_info['metadata']['mae']:,.0f}")
else:
    st.sidebar.error("⚠️ API Offline")
    st.sidebar.info("Start API: `uvicorn backend.app.main:app --reload`")


st.header("📝 Claim Information")

# Clean, focused layout
col1, col2 = st.columns(2)

with col1:
    st.subheader("🚙 Vehicle Information")
    auto_make = st.selectbox("Make", [
        "BMW", "Mercedes", "Audi", "Lexus", "Porsche", "Tesla",
        "Toyota", "Honda", "Ford", "Chevrolet", "Nissan", "Mazda",
        "Dodge", "Jeep", "Ram", "GMC", "Hyundai", "Kia", "Subaru"
    ])
    auto_model = st.text_input("Model", value="M4", help="e.g., M4, Camry, Mustang")
    auto_year = st.number_input("Year", min_value=2000, max_value=2025, value=2024)

    st.subheader("📍 Location")
    incident_state = st.selectbox("State", [
        "NY", "CA", "TX", "FL", "IL", "PA", "OH", "NC", "SC", "VA",
        "WV", "GA", "MI", "NJ", "AZ", "WA", "MA", "TN", "IN", "MO"
    ])

with col2:
    st.subheader("💥 Accident Details")
    incident_severity = st.selectbox("Damage Severity", [
        "Minor Damage",
        "Major Damage",
        "Total Loss",
        "Trivial Damage"
    ])

    collision_type = st.selectbox("Collision Type", [
        "Front Collision",
        "Rear Collision",
        "Side Collision",
        "Unknown"
    ])

    bodily_injuries = st.number_input("Bodily Injuries", min_value=0, max_value=10, value=0,
                                     help="Number of people injured")

    st.subheader("💰 Policy Information")
    policy_deductable = st.selectbox("Deductible", [500, 1000, 1500, 2000, 2500], index=1)
    policy_annual_premium = st.number_input("Annual Premium ($)", min_value=500.0, max_value=10000.0, value=1500.0, step=100.0)

    # Optional fields (collapsed)
    with st.expander("⚙️ Additional Details (Optional)"):
        age = st.number_input("Driver Age", min_value=16, max_value=100, value=35)
        months_as_customer = st.number_input("Months as Customer", min_value=0, value=36)
        witnesses = st.number_input("Witnesses", min_value=0, max_value=10, value=0)
        police_report_available = st.selectbox("Police Report?", ["YES", "NO"])


# Predict button
st.markdown("---")
if st.button("💰 Estimate Repair Cost", type="primary", use_container_width=True):

    features = {
        # Vehicle
        "auto_make": auto_make,
        "auto_model": auto_model,
        "auto_year": auto_year,

        # Incident
        "incident_severity": incident_severity,
        "collision_type": collision_type,
        "incident_state": incident_state,
        "incident_type": "Single Vehicle Collision",  # Default
        "bodily_injuries": bodily_injuries,
        "witnesses": witnesses,
        "police_report_available": police_report_available,

        # Policy
        "policy_state": incident_state,
        "policy_deductable": policy_deductable,
        "policy_annual_premium": policy_annual_premium,
        "months_as_customer": months_as_customer,
        "age": age,

        # Defaults (not relevant for prediction, but model expects them)
        "policy_number": 0,
        "policy_bind_date": "2020-01-01",
        "policy_csl": "250/500",
        "umbrella_limit": 0,
        "insured_zip": 10001,
        "insured_sex": "MALE",
        "insured_education_level": "College",
        "insured_occupation": "other",
        "insured_hobbies": "other",  # No more "sleeping" BS
        "insured_relationship": "self",
        "capital-gains": 0,
        "capital-loss": 0,
        "incident_date": datetime.now().strftime("%Y-%m-%d"),
        "authorities_contacted": "Police" if police_report_available == "YES" else "None",
        "incident_city": "City",
        "incident_location": "Street",
        "incident_hour_of_the_day": 14,
        "number_of_vehicles_involved": 1,
        "property_damage": "NO",
        "injury_claim": 0,
        "property_claim": 0,
        "vehicle_claim": 0,
        "fraud_reported": "N"
    }

    with st.spinner("Calculating estimate..."):
        result = predict_cost(features)

    if "error" in result:
        st.error(f"❌ Error: {result['error']}")
    else:
        predicted_cost = result["predicted_cost"]
        vehicle_value = result.get("estimated_vehicle_value", 0)
        confidence = result.get("confidence", "medium")
        reasoning = result.get("reasoning", [])

        # Display results
        st.success("✅ Estimate Complete")

        # Main metrics
        cols = st.columns(4)
        with cols[0]:
            st.metric("🔧 Estimated Repair Cost", f"${predicted_cost:,.2f}")
        with cols[1]:
            st.metric("🚗 Est. Vehicle Value", f"${vehicle_value:,.0f}")
        with cols[2]:
            st.metric("💵 Your Deductible", f"${policy_deductable:,.2f}")
        with cols[3]:
            insurance_pays = max(0, predicted_cost - policy_deductable)
            st.metric("🏦 Insurance Covers", f"${insurance_pays:,.2f}")

        # Breakdown
        st.markdown("---")
        st.subheader("📊 Cost Breakdown")

        if predicted_cost > policy_deductable:
            st.info(f"💡 **Recommendation:** File a claim. Insurance will cover ${insurance_pays:,.2f} after your ${policy_deductable:,.2f} deductible.")
        else:
            st.warning(f"💡 **Recommendation:** Cost is below your deductible. Consider paying out-of-pocket to avoid premium increases.")

        # Confidence & reasoning
        confidence_emoji = {"high": "🟢", "medium": "🟡", "low": "🔴"}
        st.markdown(f"**Model Confidence:** {confidence_emoji.get(confidence, '🟡')} {confidence.title()}")

        if reasoning:
            with st.expander("📋 How we calculated this"):
                for r in reasoning:
                    st.markdown(f"• {r}")

        # Valuation details
        if "valuation_details" in result:
            details = result["valuation_details"]
            with st.expander("🔍 Vehicle Valuation Details"):
                st.json(details)


# Footer
st.markdown("---")
st.caption("RepairHelper • Powered by ML • Estimates are for informational purposes only")
