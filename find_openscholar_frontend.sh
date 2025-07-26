#!/bin/bash
# find_openscholar_frontend.sh - Find the correct OpenScholar frontend

echo "🔍 Finding OpenScholar Frontend"
echo "==============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check what's running on common ports
echo "🔍 Checking what's running on common ports..."
echo ""

for port in {3000..3010}; do
    if lsof -i :$port > /dev/null 2>&1; then
        PROCESS_INFO=$(lsof -i :$port | tail -n 1)
        echo "Port $port: $PROCESS_INFO"
        
        # Test if it's OpenScholar by checking for specific content
        if curl -s http://localhost:$port | grep -q "OpenScholar"; then
            print_success "Found OpenScholar frontend on port $port!"
            OPENSCHOLAR_PORT=$port
        elif curl -s http://localhost:$port | grep -q "resume\|portfolio\|CV"; then
            print_warning "Found resume/portfolio site on port $port"
        else
            print_info "Found some other service on port $port"
        fi
    fi
done

echo ""

# Check if OpenScholar frontend was found
if [ -n "$OPENSCHOLAR_PORT" ]; then
    print_success "🎉 OpenScholar frontend is running on port $OPENSCHOLAR_PORT"
    print_success "Access it at: http://localhost:$OPENSCHOLAR_PORT"
    
    # Try to open it
    if command -v open &> /dev/null; then
        print_info "Opening OpenScholar in your browser..."
        open http://localhost:$OPENSCHOLAR_PORT
    fi
else
    print_error "OpenScholar frontend not found on any port"
    print_info "Let's start it on a different port..."
    
    # Find a free port for OpenScholar
    for port in {3001..3010}; do
        if ! lsof -i :$port > /dev/null 2>&1; then
            FREE_PORT=$port
            break
        fi
    done
    
    if [ -n "$FREE_PORT" ]; then
        print_info "Starting OpenScholar frontend on port $FREE_PORT..."
        
        # Start the frontend on the free port
        cd frontend
        export PORT=$FREE_PORT
        export REACT_APP_API_URL=http://localhost:8000
        
        print_info "Starting React development server..."
        print_info "This will take about 30-60 seconds..."
        
        npm start &
        FRONTEND_PID=$!
        
        # Wait for it to start
        echo "Waiting for frontend to start..."
        for i in {1..60}; do
            if curl -s http://localhost:$FREE_PORT > /dev/null 2>&1; then
                if curl -s http://localhost:$FREE_PORT | grep -q "OpenScholar"; then
                    print_success "🎉 OpenScholar frontend is now running on port $FREE_PORT!"
                    print_success "Access it at: http://localhost:$FREE_PORT"
                    
                    # Try to open it
                    if command -v open &> /dev/null; then
                        open http://localhost:$FREE_PORT
                    fi
                    break
                fi
            fi
            sleep 1
        done
        
        if [ $i -eq 60 ]; then
            print_error "Frontend didn't start properly"
            kill $FRONTEND_PID 2>/dev/null
        fi
    else
        print_error "No free ports available"
    fi
fi

echo ""
echo "📊 Port Summary:"
echo "================"
echo "Your resume site is likely on port 3000"
echo "OpenScholar should be on a different port (3001-3010)"
echo ""
echo "🔧 If you need to stop your resume site:"
echo "lsof -i :3000  # Find the process"
echo "kill [PID]     # Kill the process"
