#!/bin/bash
# quick_start_guide.sh - Quick start guide for using OpenScholar

echo "🎯 OpenScholar User Guide - Getting Started"
echo "==========================================="

# Check if application is running
echo "🔍 Checking if OpenScholar is running..."

BACKEND_FOUND=false
FRONTEND_FOUND=false
BACKEND_PORT=""
FRONTEND_PORT=""

# Check backend
for port in {8000..8010}; do
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        BACKEND_PORT=$port
        BACKEND_FOUND=true
        echo "✅ Backend API running on port $port"
        break
    fi
done

# Check frontend
for port in {3000..3010}; do
    if curl -s http://localhost:$port > /dev/null 2>&1; then
        FRONTEND_PORT=$port
        FRONTEND_FOUND=true
        echo "✅ Frontend running on port $port"
        break
    fi
done

if [ "$BACKEND_FOUND" = true ] && [ "$FRONTEND_FOUND" = true ]; then
    echo ""
    echo "🎉 OpenScholar is running!"
    echo "========================="
    echo ""
    echo "🌐 Main Application: http://localhost:$FRONTEND_PORT"
    echo "🔧 API Backend: http://localhost:$BACKEND_PORT"
    echo "📋 API Health: http://localhost:$BACKEND_PORT/health"
    echo "📖 API Docs: http://localhost:$BACKEND_PORT/docs"
    echo ""
    echo "🚀 Ready to use OpenScholar!"
    echo ""
    echo "📚 Quick Start Steps:"
    echo "1. Open http://localhost:$FRONTEND_PORT in your browser"
    echo "2. Try searching for: 'machine learning education'"
    echo "3. Click 'Register' to create an account"
    echo "4. Save papers to collections"
    echo "5. Export your research"
    echo ""
    
    # Try to open in browser (macOS)
    if command -v open &> /dev/null; then
        echo "🌐 Opening OpenScholar in your browser..."
        open http://localhost:$FRONTEND_PORT
    fi
    
elif [ "$BACKEND_FOUND" = true ]; then
    echo "⚠️  Backend is running but frontend is not"
    echo "Start frontend: ./start_frontend.sh"
elif [ "$FRONTEND_FOUND" = true ]; then
    echo "⚠️  Frontend is running but backend is not"
    echo "Start backend: python run_auto_port.py"
else
    echo "❌ OpenScholar is not running"
    echo "Start both: ./start_openscholar.sh"
fi
