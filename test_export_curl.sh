#!/bin/bash
# Test script for OpenScholar export API endpoint

echo "🧪 Testing OpenScholar Export API Endpoint"
echo "=========================================="

# Sample papers data for testing
SAMPLE_DATA='{
  "papers": [
    {
      "title": "The role of nutrition in early development",
      "authors": ["Smith, John", "Doe, Jane"],
      "abstract": "This study examines the critical role of nutrition in early childhood development and its long-term impacts on cognitive and physical growth.",
      "year": "2021",
      "source": "Europe PMC",
      "doi": "10.1234/abc123",
      "full_text_url": "https://example.com/paper1.pdf",
      "journal": "Journal of Early Childhood Research"
    },
    {
      "title": "Educational interventions for healthy eating habits",
      "authors": ["Johnson, Mary", "Brown, David"],
      "abstract": "An analysis of educational programs designed to promote healthy eating habits in school-age children.",
      "year": "2022",
      "source": "ERIC",
      "doi": "10.5678/def456",
      "full_text_url": "https://example.com/paper2.pdf",
      "journal": "Educational Psychology Review"
    }
  ],
  "format": "bib"
}'

echo "📄 Testing BibTeX export..."
echo "Request data:"
echo "$SAMPLE_DATA" | jq .

echo ""
echo "🌐 Making API request..."

# Test the export endpoint
curl -X POST "http://localhost:8001/export" \
  -H "Content-Type: application/json" \
  -d "$SAMPLE_DATA" \
  -o "test_export_output.bib" \
  -w "HTTP Status: %{http_code}\nContent-Type: %{content_type}\nFile Size: %{size_download} bytes\n"

echo ""
echo "📁 Generated file content:"
echo "========================="
cat test_export_output.bib

echo ""
echo "✅ Test completed! Check test_export_output.bib for the exported content."