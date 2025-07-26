#!/bin/bash
# test_setup.sh - Setup and test OpenScholar

echo "🔧 Setting up OpenScholar for testing..."

# Navigate to project directory
cd /Users/tristonmiller/Desktop/SwiftBarPlugins1/OpenScholar || exit 1

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Setup database
echo "Setting up database..."
python database_setup.py setup

# Run basic tests
echo "Running basic component tests..."
python basic_test.py

echo "Setup complete!"
