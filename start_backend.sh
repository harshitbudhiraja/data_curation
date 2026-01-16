#!/bin/bash

# Start FastAPI backend server
echo "🚀 Starting FastAPI backend on http://localhost:8000"
source venv/bin/activate
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
