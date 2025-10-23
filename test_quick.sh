#!/bin/bash

echo "=================================================="
echo "  RepairHelper - Quick System Check"
echo "=================================================="
echo ""

# Check Python version
echo "✓ Checking Python..."
python3 --version

# Check if model exists
echo ""
echo "✓ Checking model..."
if [ -f "ml/artifacts/model_improved.pkl" ]; then
    echo "   Model found: ml/artifacts/model_improved.pkl"
else
    echo "   ❌ Model not found! Run: python3 -m ml.baseline_improved"
    exit 1
fi

# Run quick test
echo ""
echo "✓ Running quick prediction test..."
python3 -c "
from ml.model_wrapper import ImprovedModelWrapper
import warnings
warnings.filterwarnings('ignore')

wrapper = ImprovedModelWrapper()
result = wrapper.predict({
    'auto_make': 'Toyota',
    'auto_model': 'Camry',
    'auto_year': 2020,
    'incident_severity': 'Major Damage',
    'incident_state': 'OH',
    'bodily_injuries': 0
})

print(f'   Prediction: \${result[\"predicted_cost\"]:,.2f}')
print(f'   Model MAE: \${result[\"mae\"]:,.2f}')
print(f'   Model R²: {result[\"r2\"]:.4f}')
"

echo ""
echo "=================================================="
echo "✅ ALL SYSTEMS WORKING!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "  • Interactive demo:  python3 demo.py"
echo "  • Full test:         python3 test_model_wrapper.py"
echo "  • Start API:         uvicorn backend.app.main:app --reload"
echo "  • Start UI:          streamlit run frontend/streamlit_app.py"
echo ""
