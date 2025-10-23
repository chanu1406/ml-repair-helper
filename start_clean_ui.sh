#!/bin/bash

echo "=================================================="
echo "  Starting RepairHelper (Clean UI)"
echo "=================================================="
echo ""

# Check if we're in the right directory
if [ ! -f "frontend/streamlit_app_clean.py" ]; then
    echo "❌ Error: Must run from project root directory"
    echo "   cd /Users/chanuollala/Documents/ML/repair-helper-clean"
    exit 1
fi

echo "✓ Starting clean frontend (no BS fields!)..."
echo ""
echo "📝 What's different in the clean UI:"
echo "   ✅ Only essential fields (vehicle, damage, location)"
echo "   ❌ Removed: hobbies, occupation, education, etc."
echo "   🎯 Cleaner, faster, more accurate"
echo ""
echo "Opening UI at: http://localhost:8501"
echo ""

streamlit run frontend/streamlit_app_clean.py
