#!/bin/bash

echo "🚀 Starting Meeting Minutes Backend..."
echo ""

cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/bin/uvicorn" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo ""
echo "✅ Backend starting on http://localhost:8000"
echo "📝 API docs available at http://localhost:8000/docs"
echo ""

python main.py
