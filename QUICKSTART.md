# QuickStart Guide - RepairHelper

## How to Test and Run the Application

### Prerequisites
✅ **Already done for you:**
- Python 3.9+ installed
- All dependencies installed (`pip3 install -r requirements.txt`)
- Improved model trained and ready

---

## 1. Test the Improved Model

### Quick Test (30 seconds)
```bash
# Test that everything works
python3 test_model_wrapper.py
```

**What this does:**
- Loads the improved model
- Makes sample predictions
- Tests different damage severities
- Compares luxury vs regular vehicles

**Expected output:**
```
✓ Loaded improved model (MAE: $740.60)
🎯 Predicted Cost: $56,269.72
✅ MODEL WRAPPER WORKING CORRECTLY
```

### Full System Test
```bash
# Run complete test suite
python3 test_system.py
```

**What this tests:**
- NHTSA VIN decoding
- Database initialization
- Valuation service
- Business rules integration

---

## 2. Run the Backend API

### Start the FastAPI Server

**Option A: Using the start script**
```bash
chmod +x start_api.sh
./start_api.sh
```

**Option B: Manual start**
```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Test the API

**Open your browser:**
- API Documentation: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

**Test with curl:**
```bash
# Health check
curl http://localhost:8000/health

# Model info
curl http://localhost:8000/model-info

# Decode a VIN
curl "http://localhost:8000/vehicle/decode/4T1B11HK5KU211111"
```

### Make a Prediction

**Using the API docs (easiest):**
1. Go to http://localhost:8000/docs
2. Click on `POST /predict`
3. Click "Try it out"
4. Paste this example:

```json
{
  "auto_make": "Toyota",
  "auto_model": "Camry",
  "auto_year": 2018,
  "incident_severity": "Major Damage",
  "collision_type": "Front Collision",
  "policy_state": "OH",
  "incident_state": "OH",
  "bodily_injuries": 0,
  "witnesses": 2,
  "police_report_available": "YES",
  "property_damage": "NO",
  "months_as_customer": 36,
  "age": 35,
  "policy_deductable": 1000,
  "policy_annual_premium": 1200
}
```

5. Click "Execute"

**Using curl:**
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "auto_make": "Toyota",
    "auto_model": "Camry",
    "auto_year": 2018,
    "incident_severity": "Major Damage",
    "collision_type": "Front Collision",
    "policy_state": "OH",
    "bodily_injuries": 0
  }'
```

---

## 3. Run the Frontend UI

### Start Streamlit

**In a new terminal:**
```bash
streamlit run frontend/streamlit_app.py
```

**Expected output:**
```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

### Use the UI

1. **Open browser:** http://localhost:8501
2. **Fill in the claim form:**
   - Vehicle information (make, model, year)
   - Incident details (severity, type, location)
   - Policy information
3. **Click "Predict Cost"**
4. **View results:**
   - Predicted repair cost
   - Estimated vehicle value
   - Reasoning breakdown
   - Deductible calculation

---

## 4. Test Different Scenarios

### Scenario 1: Minor Fender Bender
```bash
python3 -c "
from ml.model_wrapper import ImprovedModelWrapper

wrapper = ImprovedModelWrapper()
result = wrapper.predict({
    'auto_make': 'Honda',
    'auto_model': 'Civic',
    'auto_year': 2020,
    'incident_severity': 'Minor Damage',
    'collision_type': 'Rear Collision',
    'incident_state': 'OH',
    'bodily_injuries': 0,
    'policy_deductable': 500,
    'policy_annual_premium': 1000,
    'months_as_customer': 24,
    'age': 28
})

print(f'Minor damage - Honda Civic: \${result[\"predicted_cost\"]:,.2f}')
"
```

### Scenario 2: Major Accident with Injuries
```bash
python3 -c "
from ml.model_wrapper import ImprovedModelWrapper

wrapper = ImprovedModelWrapper()
result = wrapper.predict({
    'auto_make': 'BMW',
    'auto_model': '3 Series',
    'auto_year': 2019,
    'incident_severity': 'Major Damage',
    'collision_type': 'Front Collision',
    'incident_state': 'NY',
    'bodily_injuries': 2,
    'policy_deductable': 1000,
    'policy_annual_premium': 2000,
    'months_as_customer': 48,
    'age': 42
})

print(f'Major damage + injuries - BMW: \${result[\"predicted_cost\"]:,.2f}')
"
```

### Scenario 3: Total Loss
```bash
python3 -c "
from ml.model_wrapper import ImprovedModelWrapper

wrapper = ImprovedModelWrapper()
result = wrapper.predict({
    'auto_make': 'Toyota',
    'auto_model': 'RAV4',
    'auto_year': 2015,
    'incident_severity': 'Total Loss',
    'collision_type': 'Side Collision',
    'incident_state': 'SC',
    'bodily_injuries': 1,
    'policy_deductable': 500,
    'policy_annual_premium': 1500,
    'months_as_customer': 60,
    'age': 35
})

print(f'Total loss - Toyota RAV4: \${result[\"predicted_cost\"]:,.2f}')
"
```

---

## 5. Compare Baseline vs Improved Model

### Run Comparison Script
```bash
python3 -c "
from ml.model_wrapper import ImprovedModelWrapper
import joblib
import pandas as pd

# Sample claim
claim = {
    'auto_make': 'Toyota',
    'auto_model': 'Camry',
    'auto_year': 2018,
    'incident_severity': 'Major Damage',
    'collision_type': 'Front Collision',
    'incident_state': 'OH',
    'bodily_injuries': 0,
    'months_as_customer': 36,
    'age': 35,
    'policy_deductable': 1000,
    'policy_annual_premium': 1200
}

# Improved model
improved = ImprovedModelWrapper()
improved_pred = improved.predict(claim)

# Baseline model (if you want to compare)
print('=' * 50)
print('MODEL COMPARISON')
print('=' * 50)
print(f'Improved Model:')
print(f'  Predicted Cost: \${improved_pred[\"predicted_cost\"]:,.2f}')
print(f'  Model MAE: \${improved_pred[\"mae\"]:,.2f}')
print(f'  Model R²: {improved_pred[\"r2\"]:.4f}')
print(f'  Model MAPE: {improved_pred[\"mape\"]:.2f}%')
print()
print('Improvements:')
print('  • 11 engineered features')
print('  • Data-driven business rules')
print('  • Optimized hyperparameters')
print('  • 4% reduction in MAE')
"
```

---

## 6. Test VIN Decoding (Real-Time API)

```bash
python3 -c "
from backend.app.nhtsa_service import get_nhtsa_service

nhtsa = get_nhtsa_service()

# Test VINs
test_vins = [
    '4T1B11HK5KU211111',  # Toyota Camry
    '1HGBH41JXMN109186',  # Honda Accord
    '5UXWX7C5*BA',        # BMW X3
]

print('Testing NHTSA VIN Decoder:')
print('=' * 60)

for vin in test_vins:
    try:
        data = nhtsa.decode_vin(vin)
        print(f'VIN: {vin}')
        print(f'  {data.get(\"year\")} {data.get(\"make\")} {data.get(\"model\")}')
        print(f'  Trim: {data.get(\"trim\")}')
        print()
    except Exception as e:
        print(f'VIN: {vin} - Error: {e}')
        print()
"
```

---

## 7. Explore the Data and Model

### View Training Data
```bash
python3 -c "
import pandas as pd

# Load the dataset
df = pd.read_csv('data/raw/insurance_claims.csv')

print('Dataset Overview:')
print(f'  Rows: {len(df):,}')
print(f'  Columns: {len(df.columns)}')
print()

print('Sample Claims:')
print(df[['auto_make', 'auto_model', 'auto_year', 'incident_severity', 'total_claim_amount']].head(10))
print()

print('Average Claim by Severity:')
print(df.groupby('incident_severity')['total_claim_amount'].mean().sort_values())
"
```

### View Model Features
```bash
python3 -c "
import json

# Load model metadata
with open('ml/artifacts/model_improved_metadata.json') as f:
    meta = json.load(f)

print('Improved Model Details:')
print('=' * 50)
print(f'  Features: {meta[\"features_count\"]}')
print(f'  Training samples: {meta[\"training_samples\"]:,}')
print(f'  Validation samples: {meta[\"validation_samples\"]:,}')
print()
print('Performance Metrics:')
print(f'  MAE: \${meta[\"mae\"]:,.2f}')
print(f'  RMSE: \${meta[\"rmse\"]:,.2f}')
print(f'  R²: {meta[\"r2\"]:.4f}')
print(f'  Median AE: \${meta[\"median_ae\"]:,.2f}')
print(f'  MAPE: {meta[\"mape\"]:.2f}%')
"
```

### View Business Rules
```bash
python3 -c "
import json

# Load business rules
with open('ml/artifacts/business_rules.json') as f:
    rules = json.load(f)

print('Data-Driven Business Rules:')
print('=' * 50)

print('\nRegional Multipliers:')
for state, mult in sorted(rules['regional_multipliers'].items(), key=lambda x: x[1], reverse=True):
    print(f'  {state}: {mult:.2f}x')

print('\nSeverity Ratios (% of vehicle value):')
for severity, ratio in sorted(rules['severity_ratios'].items(), key=lambda x: x[1]):
    print(f'  {severity}: {ratio:.1%}')

print('\nCollision Type Multipliers:')
for col_type, mult in sorted(rules['collision_type_multipliers'].items(), key=lambda x: x[1], reverse=True):
    print(f'  {col_type}: {mult:.2f}x')
"
```

---

## 8. Run Everything Together

### Full Stack Demo

**Terminal 1 - Start Backend:**
```bash
uvicorn backend.app.main:app --reload --port 8000
```

**Terminal 2 - Start Frontend:**
```bash
streamlit run frontend/streamlit_app.py
```

**Terminal 3 - Test API:**
```bash
# Wait for servers to start, then test
sleep 5

# Test health
curl http://localhost:8000/health

# Test prediction
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "auto_make": "Toyota",
    "auto_model": "Camry",
    "auto_year": 2020,
    "incident_severity": "Minor Damage",
    "policy_state": "OH"
  }'
```

---

## 9. Troubleshooting

### Issue: Port already in use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 8501
lsof -ti:8501 | xargs kill -9
```

### Issue: Module not found
```bash
# Ensure you're in the project root
cd /Users/chanuollala/Documents/ML/repair-helper-clean

# Reinstall dependencies
pip3 install -r requirements.txt
```

### Issue: Database locked
```bash
# Remove old database
rm -f vehicle_data.db

# Restart API (will recreate DB)
uvicorn backend.app.main:app --reload
```

### Issue: Model not found
```bash
# Check model exists
ls -lh ml/artifacts/model_improved.pkl

# If missing, retrain
python3 -m ml.baseline_improved
```

---

## 10. Next Steps

### Want to improve accuracy further?

1. **Read the full guide:** [ACCURACY_IMPROVEMENTS_SUMMARY.md](ACCURACY_IMPROVEMENTS_SUMMARY.md)

2. **Collect more data:** Add more insurance claims to `data/raw/`

3. **Retrain with more data:**
   ```bash
   python3 -m ml.baseline_improved
   ```

4. **Try different models:**
   - Modify `ml/baseline_improved.py`
   - Try XGBoost, LightGBM, etc.

5. **Deploy to production:**
   - Set up PostgreSQL database
   - Add authentication
   - Configure monitoring

---

## Quick Reference

| Task | Command |
|------|---------|
| Test model | `python3 test_model_wrapper.py` |
| Test system | `python3 test_system.py` |
| Start API | `uvicorn backend.app.main:app --reload` |
| Start UI | `streamlit run frontend/streamlit_app.py` |
| Retrain model | `python3 -m ml.baseline_improved` |
| View docs | http://localhost:8000/docs |

---

## Questions?

- **Documentation:** See [ACCURACY_IMPROVEMENTS_SUMMARY.md](ACCURACY_IMPROVEMENTS_SUMMARY.md)
- **API Reference:** http://localhost:8000/docs (when server running)
- **Model Details:** Check `ml/artifacts/model_improved_metadata.json`
- **Business Rules:** Check `ml/artifacts/business_rules.json`

Happy testing! 🚀
