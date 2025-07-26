#!/bin/bash
# fix_port_conflict.sh - Fix port conflicts for OpenScholar

echo "🔍 Checking for processes using port 8001..."

# Find processes using port 8001
PROCESS=$(lsof -ti :8001)

if [ -z "$PROCESS" ]; then
    echo "✅ Port 8001 is available"
else
    echo "⚠️  Port 8001 is being used by process(es): $PROCESS"
    echo "📋 Process details:"
    lsof -i :8001
    
    echo ""
    echo "🔧 Killing process(es) using port 8001..."
    kill -9 $PROCESS
    
    # Wait a moment and check again
    sleep 2
    
    NEW_PROCESS=$(lsof -ti :8001)
    if [ -z "$NEW_PROCESS" ]; then
        echo "✅ Port 8001 is now available"
    else
        echo "❌ Failed to free port 8001"
        exit 1
    fi
fi

echo ""
echo "🚀 Starting OpenScholar on port 8001..."
cd /Users/tristonmiller/Desktop/SwiftBarPlugins1/OpenScholar
source venv/bin/activate
python run.py
