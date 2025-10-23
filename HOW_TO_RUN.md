# How to Run RepairHelper - Quick Guide

## 🚀 Fastest Way to Test

### 1. Interactive Demo (Recommended for First Time)
```bash
python3 demo.py
```

This gives you an interactive menu with:
- Quick demo with 3 examples
- Compare damage severities
- Compare vehicle types (economy vs luxury)
- Compare regional differences
- Make custom predictions
- View model performance
- View business rules

**Perfect for:** Understanding what the model can do

---

### 2. Quick Model Test
```bash
python3 test_model_wrapper.py
```

**What it does:**
- Loads the improved model
- Makes sample predictions
- Shows accuracy metrics
- Takes ~5 seconds

**Expected output:**
```
✓ Loaded improved model (MAE: $740.60)
🎯 Predicted Cost: $56,269.72
✅ MODEL WRAPPER WORKING CORRECTLY
```

---

### 3. Full System Test
```bash
python3 test_system.py
```

**What it tests:**
- ✅ NHTSA VIN decoding (real API)
- ✅ Database initialization
- ✅ Vehicle valuation service
- ✅ Business rules integration

**Takes:** ~10 seconds

---

## 🌐 Run the Full Application

### Backend API + Frontend UI

**Terminal 1 - Start Backend:**
```bash
uvicorn backend.app.main:app --reload --port 8000
```

**Terminal 2 - Start Frontend:**
```bash
streamlit run frontend/streamlit_app.py
```

**Then open:**
- **Frontend UI:** http://localhost:8501
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

---

## 📝 Make Predictions from Python

### Simple Example
```python
from ml.model_wrapper import ImprovedModelWrapper

# Load model (do this once)
wrapper = ImprovedModelWrapper()

# Make prediction
claim = {
    "auto_make": "Toyota",
    "auto_model": "Camry",
    "auto_year": 2020,
    "incident_severity": "Major Damage",
    "incident_state": "OH",
    "bodily_injuries": 0
}

result = wrapper.predict(claim)
print(f"Predicted cost: ${result['predicted_cost']:,.2f}")
```

### One-Liner Tests

**Minor damage:**
```bash
python3 -c "from ml.model_wrapper import ImprovedModelWrapper; w=ImprovedModelWrapper(); print(f\"\${w.predict({'auto_make':'Honda','auto_model':'Civic','auto_year':2020,'incident_severity':'Minor Damage','incident_state':'OH','bodily_injuries':0})['predicted_cost']:,.2f}\")"
```

**Major damage:**
```bash
python3 -c "from ml.model_wrapper import ImprovedModelWrapper; w=ImprovedModelWrapper(); print(f\"\${w.predict({'auto_make':'Toyota','auto_model':'Camry','auto_year':2018,'incident_severity':'Major Damage','incident_state':'NY','bodily_injuries':1})['predicted_cost']:,.2f}\")"
```

---

## 🧪 Test the API

### Using curl

**Health check:**
```bash
curl http://localhost:8000/health
```

**Model info:**
```bash
curl http://localhost:8000/model-info
```

**Decode VIN:**
```bash
curl "http://localhost:8000/vehicle/decode/4T1B11HK5KU211111"
```

**Make prediction:**
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "auto_make": "Toyota",
    "auto_model": "Camry",
    "auto_year": 2020,
    "incident_severity": "Minor Damage",
    "incident_state": "OH"
  }'
```

### Using the Interactive Docs

1. Start the API: `uvicorn backend.app.main:app --reload`
2. Go to: http://localhost:8000/docs
3. Click on any endpoint
4. Click "Try it out"
5. Enter parameters
6. Click "Execute"

---

## 📊 View Model Details

### Performance Metrics
```bash
python3 -c "
import json
with open('ml/artifacts/model_improved_metadata.json') as f:
    m = json.load(f)
print(f'MAE: \${m[\"mae\"]:,.2f}')
print(f'R²: {m[\"r2\"]:.4f}')
print(f'MAPE: {m[\"mape\"]:.2f}%')
"
```

### Business Rules
```bash
python3 -c "
import json
with open('ml/artifacts/business_rules.json') as f:
    r = json.load(f)
print('Regional Multipliers:')
for s, m in sorted(r['regional_multipliers'].items()):
    print(f'  {s}: {m:.2f}x')
"
```

---

## 🔍 Example Scenarios

### Scenario 1: Minor Fender Bender
```python
from ml.model_wrapper import ImprovedModelWrapper

wrapper = ImprovedModelWrapper()
result = wrapper.predict({
    "auto_make": "Honda",
    "auto_model": "Civic",
    "auto_year": 2021,
    "incident_severity": "Minor Damage",
    "collision_type": "Rear Collision",
    "incident_state": "OH",
    "bodily_injuries": 0
})

print(f"Minor damage: ${result['predicted_cost']:,.2f}")
```

### Scenario 2: Major Collision with Injuries
```python
result = wrapper.predict({
    "auto_make": "Toyota",
    "auto_model": "RAV4",
    "auto_year": 2019,
    "incident_severity": "Major Damage",
    "collision_type": "Front Collision",
    "incident_state": "NY",
    "bodily_injuries": 2
})

print(f"Major + injuries: ${result['predicted_cost']:,.2f}")
```

### Scenario 3: Luxury Vehicle Total Loss
```python
result = wrapper.predict({
    "auto_make": "BMW",
    "auto_model": "X5",
    "auto_year": 2022,
    "incident_severity": "Total Loss",
    "collision_type": "Side Collision",
    "incident_state": "SC",
    "bodily_injuries": 1
})

print(f"Luxury total loss: ${result['predicted_cost']:,.2f}")
```

---

## 📁 Project Files

### Key Files
- **`demo.py`** - Interactive demo (best way to start!)
- **`test_model_wrapper.py`** - Quick model test
- **`test_system.py`** - Full system test
- **`QUICKSTART.md`** - Detailed guide
- **`ACCURACY_IMPROVEMENTS_SUMMARY.md`** - Complete documentation

### Model Files
- **`ml/artifacts/model_improved.pkl`** - Trained model
- **`ml/artifacts/business_rules.json`** - Data-driven rules
- **`ml/artifacts/model_improved_metadata.json`** - Performance metrics

### Code Files
- **`ml/model_wrapper.py`** - Easy prediction interface
- **`ml/baseline_improved.py`** - Training script
- **`backend/app/main.py`** - FastAPI server
- **`frontend/streamlit_app.py`** - UI

---

## 🛠️ Troubleshooting

### "Model not found"
```bash
# Check if model exists
ls -lh ml/artifacts/model_improved.pkl

# If missing, train it
python3 -m ml.baseline_improved
```

### "Port already in use"
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 8501
lsof -ti:8501 | xargs kill -9
```

### "Module not found"
```bash
# Make sure you're in project root
pwd
# Should show: .../repair-helper-clean

# Reinstall dependencies
pip3 install -r requirements.txt
```

---

## 📚 Documentation

- **Quick Start:** See [QUICKSTART.md](QUICKSTART.md)
- **Accuracy Improvements:** See [ACCURACY_IMPROVEMENTS_SUMMARY.md](ACCURACY_IMPROVEMENTS_SUMMARY.md)
- **Vehicle Valuation:** See [VEHICLE_VALUATION_README.md](VEHICLE_VALUATION_README.md)
- **API Docs:** Run API and go to http://localhost:8000/docs

---

## 🎯 Quick Commands Cheat Sheet

```bash
# Interactive demo
python3 demo.py

# Quick test
python3 test_model_wrapper.py

# System test
python3 test_system.py

# Start API
uvicorn backend.app.main:app --reload

# Start UI
streamlit run frontend/streamlit_app.py

# Retrain model
python3 -m ml.baseline_improved

# View performance
python3 -c "import json; m=json.load(open('ml/artifacts/model_improved_metadata.json')); print(f'MAE: \${m[\"mae\"]:,.2f}, R²: {m[\"r2\"]:.4f}')"
```

---

## ✨ What's New

### Latest Update: Real Market Data Integration
- ✅ **100% accuracy improvement** for vehicle valuations (BMW M4: $38k → $78k)
- ✅ **Web scraping** from Edmunds and Google Shopping
- ✅ **Multi-layer fallback** (scraping → improved depreciation → never fails)
- ✅ **Clean UI** - removed useless fields (hobbies, occupation, etc.)

See [ACCURACY_UPDATE.md](ACCURACY_UPDATE.md) for details!

### Model Improvements
- ✅ **4% better accuracy** (MAE: $771.84 → $740.60)
- ✅ **11 engineered features** (vehicle age, claim ratios, etc.)
- ✅ **Data-driven business rules** (not hardcoded!)
- ✅ **Optimized hyperparameters** (via cross-validation)
- ✅ **Better evaluation** (RMSE, Median AE, MAPE)

---

**Need help?** Check [QUICKSTART.md](QUICKSTART.md) for detailed instructions!
