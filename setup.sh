#!/bin/bash
# Quick setup script for the vehicle valuation system

echo "=========================================="
echo "Vehicle Valuation System - Setup"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "ERROR: requirements.txt not found!"
    echo "Please run this script from the project root directory:"
    echo "  cd /Users/chanuollala/Documents/ML/repair-helper-clean"
    echo "  bash setup.sh"
    exit 1
fi

echo ""
echo "Step 1: Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo ""
echo "Step 2: Initializing database..."
python -c "from backend.app.database.session import init_db; init_db()"

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to initialize database"
    exit 1
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Run tests:       python test_quick.py"
echo "  2. Scrape data:     python run_scraper.py --make Toyota --model Camry --max-results 10"
echo "  3. Start API:       cd backend && uvicorn app.main:app --reload"
echo ""
echo "For more info, see VEHICLE_VALUATION_README.md"
echo "=========================================="
