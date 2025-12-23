#!/bin/bash

echo "🚀 Meeting Minutes App Launcher"
echo "================================"
echo ""

# Open two terminal tabs
osascript <<-SCRIPT
tell application "Terminal"
    activate
    do script "cd $(pwd) && ./start-backend.sh"
    delay 2
    do script "cd $(pwd) && ./start-frontend.sh"
end tell
SCRIPT

echo "✅ Application is starting in new terminal windows..."
echo ""
echo "📍 Backend:  http://localhost:8000"
echo "📍 Frontend: http://localhost:5173"
echo ""
