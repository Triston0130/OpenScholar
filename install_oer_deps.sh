#!/bin/bash
# Install dependencies needed for OER sources

echo "Installing OER source dependencies..."

# Install beautifulsoup4 for HTML parsing (needed by DOAB and LibreTexts)
pip3 install beautifulsoup4 --break-system-packages --user

echo "Dependencies installed!"
echo ""
echo "Now run the debug script to check if everything is working:"
echo "python3 debug_oer_error.py"