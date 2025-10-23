# How to Start the API

## ✅ Correct Way

### Step 1: Go to Project Root
```bash
cd /Users/chanuollala/Documents/ML/repair-helper-clean
```

### Step 2: Start the API
```bash
uvicorn backend.app.main:app --reload --port 8000
```

**Or use the helper script:**
```bash
chmod +x start_api.sh
./start_api.sh
```

---

## ❌ Common Mistake

**Don't do this:**
```bash
cd backend  # ❌ Wrong!
uvicorn backend.app.main:app --reload
```

**Why it fails:** When you're inside `backend/`, Python can't find the `backend` module.

---

## 📋 Complete Steps

**Terminal 1 - API:**
```bash
# Make sure you're in the right place
cd /Users/chanuollala/Documents/ML/repair-helper-clean

# Check you're in the right directory
pwd
# Should show: /Users/chanuollala/Documents/ML/repair-helper-clean

# Start API
uvicorn backend.app.main:app --reload --port 8000
```

**Terminal 2 - Frontend (optional):**
```bash
cd /Users/chanuollala/Documents/ML/repair-helper-clean
streamlit run frontend/streamlit_app.py
```

---

## 🎯 Quick Test After Starting

Once the API is running, test it:

```bash
# In another terminal
curl http://localhost:8000/health

# Or open in browser
open http://localhost:8000/docs
```

---

## 🔧 Troubleshooting

### Error: "No module named 'backend'"
**Solution:** You're in the wrong directory. Go to project root:
```bash
cd /Users/chanuollala/Documents/ML/repair-helper-clean
```

### Error: "Address already in use"
**Solution:** Port 8000 is taken. Kill it or use different port:
```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn backend.app.main:app --reload --port 8001
```

### Error: "No module named 'fastapi'"
**Solution:** Install dependencies:
```bash
pip3 install -r requirements.txt
```

---

## ✅ Expected Output

When starting successfully, you should see:
```
INFO:     Will watch for changes in these directories: ['/Users/chanuollala/Documents/ML/repair-helper-clean']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

## 🌐 API Endpoints

Once running, visit:
- **Interactive Docs:** http://localhost:8000/docs
- **Alternative Docs:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health
- **Model Info:** http://localhost:8000/model-info

---

## 📝 Quick Reference

| What | Command |
|------|---------|
| Go to project root | `cd /Users/chanuollala/Documents/ML/repair-helper-clean` |
| Check location | `pwd` |
| Start API | `uvicorn backend.app.main:app --reload --port 8000` |
| Test API | `curl http://localhost:8000/health` |
| View docs | Open http://localhost:8000/docs |
| Stop API | Press `Ctrl+C` in the terminal |
