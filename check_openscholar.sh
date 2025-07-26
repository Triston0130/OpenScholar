#!/bin/bash
# check_openscholar.sh - Check if OpenScholar is running

echo "🔍 Checking OpenScholar status..."

# Check common ports
PORTS=(8000 8001 8002 8003 8004 8005)

for port in "${PORTS[@]}"; do
    if lsof -i :$port > /dev/null 2>&1; then
        echo "✅ Found service on port $port"
        echo "📍 Trying to connect to http://localhost:$port..."
        
        # Try to get the health endpoint
        if curl -s http://localhost:$port/health > /dev/null 2>&1; then
            echo "🎉 OpenScholar is running on port $port!"
            echo "📋 Health check: http://localhost:$port/health"
            echo "📖 API docs: http://localhost:$port/docs"
            echo "🔍 Search endpoint: http://localhost:$port/search"
            
            # Show actual health status
            echo ""
            echo "🏥 Health Status:"
            curl -s http://localhost:$port/health | python -m json.tool
            exit 0
        fi
    fi
done

echo "❌ OpenScholar is not running on any common ports"
echo "💡 Try running: python run_auto_port.py"
