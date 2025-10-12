import streamlit as st
import requests
import json
from datetime import datetime


API_URL = "http://localhost:8000"


st.set_page_config(
    page_title="RepairHelper",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 RepairHelper")
st.markdown("Get instant repair cost estimates for your auto insurance claim")


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


st.sidebar.header("📊 Model Info")
model_info = get_model_info()
if model_info:
    st.sidebar.success("✅ Model loaded")
    st.sidebar.metric("R² Score", f"{model_info['metadata']['r2']:.4f}")
    st.sidebar.metric("Avg Error (MAE)", f"${model_info['metadata']['mae']:,.2f}")
else:
    st.sidebar.error("⚠️ API not available")
    st.sidebar.info("Start the backend: `python -m uvicorn backend.app.main:app --reload`")


st.header("Enter Claim Details")

col1, col2 = st.columns(2)

with col1:
    st.subheader("👤 Policy Information")
    months_as_customer = st.number_input("Months as Customer", min_value=0, value=328)
    age = st.number_input("Age", min_value=16, max_value=100, value=48)
    policy_state = st.selectbox("Policy State", ["OH", "IL", "IN", "SC", "VA", "NY", "NC"])
    policy_deductable = st.number_input("Deductible ($)", min_value=0, value=1000, step=500)
    policy_annual_premium = st.number_input("Annual Premium ($)", min_value=0.0, value=1406.91)
    umbrella_limit = st.number_input("Umbrella Limit ($)", min_value=0, value=0, step=1000000)

    st.subheader("👨 Insured Details")
    insured_sex = st.selectbox("Sex", ["MALE", "FEMALE"])
    insured_education_level = st.selectbox("Education", ["High School", "Associate", "MD", "PhD", "Masters", "College"])
    insured_occupation = st.selectbox("Occupation", ["craft-repair", "machine-op-inspct", "sales", "armed-forces", "tech-support", "exec-managerial"])
    insured_hobbies = st.selectbox("Hobbies", ["sleeping", "reading", "board-games", "chess", "cross-fit", "golf"])
    insured_relationship = st.selectbox("Relationship", ["husband", "wife", "own-child", "other-relative", "unmarried"])

with col2:
    st.subheader("🚨 Incident Details")
    incident_type = st.selectbox("Incident Type", ["Single Vehicle Collision", "Multi-vehicle Collision", "Vehicle Theft", "Parked Car"])
    collision_type = st.selectbox("Collision Type", ["Side Collision", "Rear Collision", "Front Collision", "?"])
    incident_severity = st.selectbox("Severity", ["Major Damage", "Minor Damage", "Total Loss", "Trivial Damage"])
    incident_state = st.selectbox("Incident State", ["SC", "OH", "VA", "NY", "NC", "IL", "IN"])
    incident_city = st.text_input("Incident City", value="Columbus")
    incident_hour_of_the_day = st.slider("Time of Day (Hour)", 0, 23, 5)
    authorities_contacted = st.selectbox("Authorities Contacted", ["Police", "Fire", "Ambulance", "None"])

    number_of_vehicles_involved = st.number_input("Vehicles Involved", min_value=1, max_value=4, value=1)
    bodily_injuries = st.number_input("Bodily Injuries", min_value=0, max_value=2, value=1)
    witnesses = st.number_input("Witnesses", min_value=0, max_value=3, value=2)

    property_damage = st.selectbox("Property Damage?", ["YES", "NO", "?"])
    police_report_available = st.selectbox("Police Report Available?", ["YES", "NO", "?"])

    st.subheader("🚙 Vehicle Details")
    auto_make = st.selectbox("Make", ["Saab", "Mercedes", "Dodge", "Chevrolet", "BMW", "Toyota", "Honda", "Ford", "Nissan"])
    auto_model = st.text_input("Model", value="92x")
    auto_year = st.number_input("Year", min_value=1990, max_value=2024, value=2004)


if st.button("💰 Get Repair Estimate", type="primary", use_container_width=True):

    features = {
        "months_as_customer": months_as_customer,
        "age": age,
        "policy_number": 0,
        "policy_bind_date": "2014-10-17",
        "policy_state": policy_state,
        "policy_csl": "250/500",
        "policy_deductable": policy_deductable,
        "policy_annual_premium": policy_annual_premium,
        "umbrella_limit": umbrella_limit,
        "insured_zip": 466132,
        "insured_sex": insured_sex,
        "insured_education_level": insured_education_level,
        "insured_occupation": insured_occupation,
        "insured_hobbies": insured_hobbies,
        "insured_relationship": insured_relationship,
        "capital-gains": 0,
        "capital-loss": 0,
        "incident_date": datetime.now().strftime("%Y-%m-%d"),
        "incident_type": incident_type,
        "collision_type": collision_type,
        "incident_severity": incident_severity,
        "authorities_contacted": authorities_contacted,
        "incident_state": incident_state,
        "incident_city": incident_city,
        "incident_location": "Main St",
        "incident_hour_of_the_day": incident_hour_of_the_day,
        "number_of_vehicles_involved": number_of_vehicles_involved,
        "property_damage": property_damage,
        "bodily_injuries": bodily_injuries,
        "witnesses": witnesses,
        "police_report_available": police_report_available,
        "injury_claim": 0,
        "property_claim": 0,
        "vehicle_claim": 0,
        "auto_make": auto_make,
        "auto_model": auto_model,
        "auto_year": auto_year,
        "fraud_reported": "N"
    }

    with st.spinner("Calculating repair estimate..."):
        result = predict_cost(features)

    if "error" in result:
        st.error(f"❌ Error: {result['error']}")
    else:
        predicted_cost = result["predicted_cost"]

        st.success("✅ Estimate Complete!")

        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "💵 Estimated Repair Cost",
                f"${predicted_cost:,.2f}"
            )

        with col2:
            if policy_deductable > 0:
                out_of_pocket = min(predicted_cost, policy_deductable)
                st.metric(
                    "Your Deductible",
                    f"${out_of_pocket:,.2f}"
                )

        with col3:
            if predicted_cost > policy_deductable:
                insurance_pays = predicted_cost - policy_deductable
                st.metric(
                    "Insurance Covers",
                    f"${insurance_pays:,.2f}"
                )
            else:
                st.metric(
                    "Insurance Covers",
                    "$0.00"
                )

        st.markdown("---")

        if predicted_cost < policy_deductable:
            st.info(f"💡 **Recommendation:** Consider paying out of pocket (${predicted_cost:,.2f}) since it's less than your deductible (${policy_deductable:,.2f})")
        else:
            st.info(f"💡 **Recommendation:** File a claim. Insurance will cover ${predicted_cost - policy_deductable:,.2f} after your ${policy_deductable:,.2f} deductible.")


st.markdown("---")
st.caption("RepairHelper uses machine learning to estimate repair costs. Estimates are for informational purposes only.")
