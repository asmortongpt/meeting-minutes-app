#!/bin/bash

echo "🎨 Starting Meeting Minutes Frontend..."
echo ""

cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

echo ""
echo "✅ Frontend starting on http://localhost:5173"
echo ""

npm run dev
