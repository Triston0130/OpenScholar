#!/bin/bash
# run_tests.sh - Comprehensive test runner for OpenScholar

echo "🧪 OpenScholar Test Suite Runner"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_warning "Virtual environment not found. Creating one..."
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    print_status "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if pytest is installed
if ! python -c "import pytest" 2>/dev/null; then
    print_warning "Installing test dependencies..."
    pip install pytest pytest-asyncio pytest-cov pytest-mock httpx
fi

# Create test results directory
mkdir -p test_results

print_status "Running OpenScholar test suite..."
echo ""

# Run different test categories
echo "1️⃣ Running Security Tests..."
python -m pytest tests/test_security_validation.py -v --tb=short -m "security or unit" \
    --cov=app.security --cov-report=html:test_results/security_coverage \
    --junitxml=test_results/security_results.xml

security_exit_code=$?

echo ""
echo "2️⃣ Running Cache System Tests..."
python -m pytest tests/test_cache_system.py -v --tb=short -m "cache or unit" \
    --cov=app.cache --cov-report=html:test_results/cache_coverage \
    --junitxml=test_results/cache_results.xml

cache_exit_code=$?

echo ""
echo "3️⃣ Running API Endpoint Tests..."
python -m pytest tests/test_api_endpoints.py -v --tb=short -m "api or integration" \
    --cov=app.main --cov-report=html:test_results/api_coverage \
    --junitxml=test_results/api_results.xml

api_exit_code=$?

echo ""
echo "4️⃣ Running Logging System Tests..."
python -m pytest tests/test_logging_system.py -v --tb=short -m "logging or unit" \
    --cov=app.logging --cov-report=html:test_results/logging_coverage \
    --junitxml=test_results/logging_results.xml

logging_exit_code=$?

echo ""
echo "5️⃣ Running Frontend Component Tests..."
python -m pytest tests/test_frontend_components.py -v --tb=short \
    --junitxml=test_results/frontend_results.xml

frontend_exit_code=$?

echo ""
echo "6️⃣ Running Complete Test Suite with Coverage..."
python -m pytest tests/ -v --tb=short \
    --cov=app --cov-report=html:test_results/full_coverage \
    --cov-report=term-missing --cov-fail-under=70 \
    --junitxml=test_results/full_results.xml

full_exit_code=$?

echo ""
echo "📊 Test Results Summary"
echo "======================="

# Check individual test results
if [ $security_exit_code -eq 0 ]; then
    print_success "Security Tests: PASSED"
else
    print_error "Security Tests: FAILED"
fi

if [ $cache_exit_code -eq 0 ]; then
    print_success "Cache Tests: PASSED"
else
    print_error "Cache Tests: FAILED"
fi

if [ $api_exit_code -eq 0 ]; then
    print_success "API Tests: PASSED"
else
    print_error "API Tests: FAILED"
fi

if [ $logging_exit_code -eq 0 ]; then
    print_success "Logging Tests: PASSED"
else
    print_error "Logging Tests: FAILED"
fi

if [ $frontend_exit_code -eq 0 ]; then
    print_success "Frontend Tests: PASSED"
else
    print_error "Frontend Tests: FAILED"
fi

echo ""
if [ $full_exit_code -eq 0 ]; then
    print_success "🎉 All tests passed! Coverage report available at test_results/full_coverage/index.html"
    
    # Display coverage summary
    echo ""
    print_status "Coverage Summary:"
    python -m pytest --cov=app --cov-report=term-missing --quiet tests/ | grep -E "(TOTAL|Name)"
    
else
    print_error "❌ Some tests failed. Check the detailed output above."
    echo ""
    print_status "Test results and coverage reports saved to test_results/ directory"
    echo "  - Full coverage: test_results/full_coverage/index.html"
    echo "  - Security coverage: test_results/security_coverage/index.html" 
    echo "  - Cache coverage: test_results/cache_coverage/index.html"
    echo "  - API coverage: test_results/api_coverage/index.html"
    echo "  - Logging coverage: test_results/logging_coverage/index.html"
fi

echo ""
print_status "Running style and security checks..."

# Check if flake8 is available for style checking
if command -v flake8 &> /dev/null; then
    echo "📝 Running style checks..."
    flake8 app/ --max-line-length=100 --ignore=E203,W503
    style_exit_code=$?
    
    if [ $style_exit_code -eq 0 ]; then
        print_success "Style checks: PASSED"
    else
        print_warning "Style checks: Some issues found"
    fi
else
    print_warning "flake8 not found - skipping style checks"
fi

# Check if bandit is available for security scanning
if command -v bandit &> /dev/null; then
    echo "🔒 Running security checks..."
    bandit -r app/ -f json -o test_results/security_scan.json
    security_scan_exit_code=$?
    
    if [ $security_scan_exit_code -eq 0 ]; then
        print_success "Security scan: PASSED"
    else
        print_warning "Security scan: Some issues found - check test_results/security_scan.json"
    fi
else
    print_warning "bandit not found - skipping security scan"
fi

echo ""
print_status "Running frontend tests (if Node.js environment available)..."

# Check if frontend tests can be run
if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
    cd frontend
    
    if command -v npm &> /dev/null; then
        print_status "Running frontend unit tests..."
        if npm test -- --watchAll=false --coverage --coverageDirectory=../test_results/frontend_coverage 2>/dev/null; then
            print_success "Frontend tests: PASSED"
        else
            print_warning "Frontend tests: Not configured or failed"
        fi
    else
        print_warning "npm not found - skipping frontend tests"
    fi
    
    cd ..
else
    print_warning "Frontend directory not found - skipping frontend tests"
fi

echo ""
echo "🏁 Test Suite Complete!"
echo "======================"

if [ $full_exit_code -eq 0 ]; then
    print_success "✅ All backend tests passed successfully!"
    echo ""
    echo "📁 Test artifacts available:"
    echo "  - Coverage reports: test_results/"
    echo "  - JUnit XML: test_results/*.xml"
    echo "  - Detailed logs: pytest output above"
    echo ""
    echo "🚀 Your OpenScholar application is test-ready!"
    exit 0
else
    print_error "❌ Some tests failed - review the output above"
    echo ""
    echo "🔧 To fix issues:"
    echo "  1. Review failed test output"
    echo "  2. Check coverage reports in test_results/"
    echo "  3. Fix any failing tests"
    echo "  4. Re-run: ./run_tests.sh"
    exit 1
fi
