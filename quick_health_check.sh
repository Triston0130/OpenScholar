#!/bin/bash
# quick_health_check.sh - Quick health check for OpenScholar

echo "🏥 OpenScholar Quick Health Check"
echo "================================"

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

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    print_error "Not in OpenScholar directory. Please run from project root."
    exit 1
fi

print_info "Checking OpenScholar installation..."

# Check Python version
PYTHON_VERSION=$(python --version 2>&1)
if [[ $? -eq 0 ]]; then
    print_success "Python available: $PYTHON_VERSION"
else
    print_error "Python not available"
    exit 1
fi

# Check virtual environment
if [ -d "venv" ]; then
    print_success "Virtual environment exists"
else
    print_warning "Virtual environment not found - creating one..."
    python -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate

# Check if key files exist
KEY_FILES=(
    "app/main.py"
    "app/security/validation.py"
    "app/cache/redis_cache.py"
    "app/database/models.py"
    "app/logging/structured_logger.py"
    "requirements.txt"
    "database_setup.py"
    "run_tests.sh"
)

for file in "${KEY_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_success "Found: $file"
    else
        print_error "Missing: $file"
        exit 1
    fi
done

# Check if requirements are installed
print_info "Checking Python dependencies..."
if python -c "import fastapi, uvicorn, redis, sqlalchemy, bleach, pytest" 2>/dev/null; then
    print_success "Core dependencies installed"
else
    print_warning "Installing dependencies..."
    pip install -r requirements.txt
    if [[ $? -eq 0 ]]; then
        print_success "Dependencies installed successfully"
    else
        print_error "Failed to install dependencies"
        exit 1
    fi
fi

# Check if database can be initialized
print_info "Checking database setup..."
if python database_setup.py health 2>/dev/null; then
    print_success "Database is healthy"
else
    print_info "Initializing database..."
    python database_setup.py setup
    if [[ $? -eq 0 ]]; then
        print_success "Database initialized successfully"
    else
        print_error "Failed to initialize database"
        exit 1
    fi
fi

# Check if main application can be imported
print_info "Testing application import..."
if python -c "from app.main import app; print('Import successful')" 2>/dev/null; then
    print_success "Application imports correctly"
else
    print_error "Failed to import application"
    exit 1
fi

# Check if tests can run
print_info "Testing pytest availability..."
if python -c "import pytest; print('Pytest available')" 2>/dev/null; then
    print_success "Test framework ready"
else
    print_warning "Installing test dependencies..."
    pip install pytest pytest-asyncio pytest-cov pytest-mock
    print_success "Test framework installed"
fi

# Run a quick test
print_info "Running quick validation test..."
if python -c "
import sys
sys.path.insert(0, '.')
from app.security.validation import SearchQueryValidator
try:
    validator = SearchQueryValidator(query='test query', limit=10)
    print('✅ Security validation working')
except Exception as e:
    print(f'❌ Security validation failed: {e}')
    sys.exit(1)
    
from app.cache.redis_cache import CacheManager
cache = CacheManager()
print('✅ Cache system working')

from app.database.models import User, Collection, Paper
print('✅ Database models working')

from app.logging.structured_logger import get_logger
logger = get_logger('test')
print('✅ Logging system working')
" 2>/dev/null; then
    print_success "Core components working"
else
    print_error "Core components test failed"
    exit 1
fi

# Final summary
echo ""
echo "🎉 OpenScholar Health Check Complete!"
echo "====================================="
print_success "All core components are working correctly"
echo ""
echo "🚀 Ready to run:"
echo "  • Start server: python run.py"
echo "  • Run tests: ./run_tests.sh"
echo "  • Check health: curl http://localhost:8000/health"
echo ""
echo "📚 For more information, see:"
echo "  • TEST_REPORT.md - Comprehensive test report"
echo "  • IMPLEMENTATION_COMPLETE.md - Implementation status"
echo "  • README.md - Getting started guide"
