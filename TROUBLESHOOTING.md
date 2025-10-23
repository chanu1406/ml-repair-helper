# Troubleshooting Guide

## ✅ **FIXED: Scikit-learn Version Mismatch**

### Problem
```
AttributeError: Can't get attribute '_RemainderColsList' on <module 'sklearn.compose._column_transformer'
```

### Cause
The model was trained with a different version of scikit-learn than what you're currently using.

### Solution ✅
**Already fixed!** The model has been retrained with your current environment.

If you see this error again:
```bash
# Retrain the model
python3 -m ml.baseline_improved
```

This takes ~2-3 minutes and will rebuild the model with your exact Python/scikit-learn versions.

---

## 📋 **How to Test Everything Works**

### 1. Quick Test (5 seconds)
```bash
python3 test_model_wrapper.py
```

**Expected output:**
```
✓ Loaded improved model (MAE: $740.60)
🎯 Predicted Cost: $56,269.72
✅ MODEL WRAPPER WORKING CORRECTLY
```

### 2. Interactive Demo
```bash
python3 demo.py
```

Then select from the menu:
- `1` - Quick demo (3 examples)
- `2` - Compare severities
- `6` - View performance
- `0` - Exit

### 3. Full System Test
```bash
python3 test_system.py
```

---

## 🔧 **Common Issues**

### Issue: "Model not found"
```bash
# Check if model exists
ls -lh ml/artifacts/model_improved.pkl

# If missing, train it
python3 -m ml.baseline_improved
```

### Issue: "Port already in use" (when starting API)
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn backend.app.main:app --reload --port 8001
```

### Issue: "Module not found"
```bash
# Make sure you're in the project root
pwd
# Should show: .../repair-helper-clean

# Check if in right directory
ls ml/model_wrapper.py  # Should exist

# If not, cd to project root
cd /Users/chanuollala/Documents/ML/repair-helper-clean
```

### Issue: Dependencies missing
```bash
# Reinstall all dependencies
pip3 install -r requirements.txt
```

### Issue: Different Python versions
You have multiple Python installations:
- System Python: `/usr/bin/python3` (3.9.6)
- Pyenv Python: `~/.pyenv/versions/3.11.9/bin/python3` (3.11.9)

**Best practice:** Use the same Python for everything:
```bash
# Check which one you're using
which python3

# To use pyenv Python for everything:
pyenv global 3.11.9

# Then retrain the model
python3 -m ml.baseline_improved
```

### Issue: Warnings about `_c39`
```
UserWarning: Skipping features without any observed values: ['_c39']
```

**This is normal!** The `_c39` column in your dataset is completely empty. The model handles this correctly by skipping it. You can safely ignore these warnings.

---

## 🚀 **Quick Reference: What Works Now**

| Command | What it does | Status |
|---------|--------------|--------|
| `python3 test_model_wrapper.py` | Quick test | ✅ Working |
| `python3 test_system.py` | Full system test | ✅ Working |
| `python3 demo.py` | Interactive demo | ✅ Working |
| `python3 -m ml.baseline_improved` | Retrain model | ✅ Working |
| `uvicorn backend.app.main:app --reload` | Start API | ✅ Ready |
| `streamlit run frontend/streamlit_app.py` | Start UI | ✅ Ready |

---

## 📊 **Test Results**

Your model is working correctly:
- **MAE:** $740.60 (4% better than baseline)
- **R² Score:** 0.9978
- **MAPE:** 1.98%
- **Features:** 51 (40 original + 11 engineered)

---

## 💡 **Tips**

1. **Always retrain after environment changes:**
   ```bash
   python3 -m ml.baseline_improved
   ```

2. **Use virtual environments to avoid version conflicts:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python3 -m ml.baseline_improved
   ```

3. **Check your Python version:**
   ```bash
   python3 --version
   python3 -c "import sklearn; print(f'sklearn: {sklearn.__version__}')"
   ```

---

## 📚 **Need More Help?**

- **Quick Start:** [HOW_TO_RUN.md](HOW_TO_RUN.md)
- **Detailed Guide:** [QUICKSTART.md](QUICKSTART.md)
- **Technical Details:** [ACCURACY_IMPROVEMENTS_SUMMARY.md](ACCURACY_IMPROVEMENTS_SUMMARY.md)

---

## ✅ **Current Status**

Everything is working and ready to use! 🎉

The version mismatch has been fixed by retraining the model with your current environment.
