#!/bin/bash
# try_openscholar.sh - Interactive demo script for OpenScholar

echo "🎯 OpenScholar Interactive Demo"
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

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_instruction() {
    echo -e "${YELLOW}👉 $1${NC}"
}

# Check if OpenScholar is running
FRONTEND_URL=""
BACKEND_URL=""

for port in {3000..3010}; do
    if curl -s http://localhost:$port > /dev/null 2>&1; then
        FRONTEND_URL="http://localhost:$port"
        break
    fi
done

for port in {8000..8010}; do
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        BACKEND_URL="http://localhost:$port"
        break
    fi
done

if [ -z "$FRONTEND_URL" ] || [ -z "$BACKEND_URL" ]; then
    echo "❌ OpenScholar is not running"
    echo "Start it with: ./start_openscholar.sh"
    exit 1
fi

print_success "OpenScholar is running!"
print_success "Frontend: $FRONTEND_URL"
print_success "Backend: $BACKEND_URL"

echo ""
echo "🎮 Let's Try OpenScholar - Follow These Steps:"
echo "=============================================="

echo ""
echo "📱 STEP 1: Open the Application"
print_instruction "Open your web browser and go to: $FRONTEND_URL"
print_info "You should see the OpenScholar homepage with a search box"

echo ""
echo "🔍 STEP 2: Try Your First Search"
print_instruction "In the search box, type: machine learning education"
print_instruction "Click 'Search Papers' or press Enter"
print_info "OpenScholar will search across 5 academic databases"
print_info "This may take 5-10 seconds for the first search"

echo ""
echo "📊 STEP 3: Explore the Results"
print_instruction "Look at the paper cards that appear"
print_instruction "Notice: Title, authors, abstract, publication year, citations"
print_instruction "Click on any DOI link to see the full paper"
print_info "Each paper shows which database it came from"

echo ""
echo "🔐 STEP 4: Create an Account (Optional)"
print_instruction "Click 'Register' in the top-right corner"
print_instruction "Fill in your details (or use demo account below)"
print_info "Demo account: demo@openscholar.com / demo123"

echo ""
echo "📚 STEP 5: Save Papers to Collections"
print_instruction "Click 'Save to Collection' on any interesting paper"
print_instruction "Create a new collection called 'My Research'"
print_instruction "Add tags like: 'important', 'to-read', 'methodology'"

echo ""
echo "🎯 STEP 6: Try Advanced Search"
print_instruction "Use the filters to narrow your search:"
print_instruction "- Set year range: 2020-2024"
print_instruction "- Publication type: Journal article"
print_instruction "- Sort by: Most cited"

echo ""
echo "📄 STEP 7: Export Papers"
print_instruction "Select some papers using 'Bulk Select'"
print_instruction "Click 'Export' and choose 'BibTeX'"
print_instruction "The file will download automatically"

echo ""
echo "🔍 STEP 8: Add External Papers"
print_instruction "Click '📄 Add Paper' in the header"
print_instruction "Try this DOI: 10.1038/nature12373"
print_instruction "Click 'Fetch Paper' to import it"

echo ""
echo "📚 STEP 9: Manage Collections"
print_instruction "Click '📚 Collections' in the header"
print_instruction "View your saved papers"
print_instruction "Edit collection names and add folders"

echo ""
echo "🎉 STEP 10: Try More Searches"
print_instruction "Try these search terms:"
print_instruction "- 'STEM education elementary school'"
print_instruction "- 'collaborative learning outcomes'"
print_instruction "- 'educational technology effectiveness'"

echo ""
echo "🚀 Quick Demo Commands:"
echo "======================"
echo ""
echo "Test the API directly:"
echo "curl -X POST $BACKEND_URL/search -H 'Content-Type: application/json' -d '{\"query\": \"test\", \"page\": 1, \"per_page\": 5}'"
echo ""
echo "Check API health:"
echo "curl $BACKEND_URL/health"
echo ""
echo "View API documentation:"
echo "Open: $BACKEND_URL/docs"

echo ""
echo "🎯 What to Expect:"
echo "=================="
print_info "Search results from 5 major academic databases"
print_info "Professional UI with paper cards and metadata"
print_info "User authentication and profile management"
print_info "Collection management for organizing papers"
print_info "Export functionality in multiple formats"
print_info "External paper import via DOI lookup"
print_info "Bulk operations for managing many papers"
print_info "Responsive design that works on all devices"

echo ""
echo "🏆 Key Features to Test:"
echo "========================"
print_info "✅ Search across ERIC, CORE, DOAJ, Europe PMC, PubMed"
print_info "✅ Advanced filters and sorting options"
print_info "✅ User registration and authentication"
print_info "✅ Collection management with tags and notes"
print_info "✅ Export to CSV, JSON, and BibTeX formats"
print_info "✅ DOI-based paper import"
print_info "✅ Bulk selection and operations"
print_info "✅ Professional search interface"

echo ""
echo "🎮 Ready to explore OpenScholar!"
echo "================================="
print_instruction "Start with: $FRONTEND_URL"
print_info "Have fun exploring your academic research platform!"

# Try to open in browser on macOS
if command -v open &> /dev/null; then
    echo ""
    echo "🌐 Opening OpenScholar in your browser..."
    open $FRONTEND_URL
fi
