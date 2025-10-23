#!/bin/bash
# Start the FastAPI server

echo "=========================================="
echo "Starting RepairHelper API Server"
echo "=========================================="
echo ""
echo "API will be available at:"
echo "  http://localhost:8000"
echo ""
echo "Interactive docs:"
echo "  http://localhost:8000/docs"
echo ""
echo "Press CTRL+C to stop"
echo "=========================================="
echo ""

# Run from project root
cd "$(dirname "$0")"
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
