#!/bin/bash
# Webmix Sync Starter GUI Launcher
# Double-click this file to start the native desktop application

cd "$(dirname "$0")"

echo "🚀 Starting Webmix Sync Starter GUI..."
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed"
    read -p "Press enter to close..."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "gui/venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv gui/venv
fi

# Activate virtual environment
source gui/venv/bin/activate

# Install/upgrade required packages
echo "🔍 Checking dependencies..."
pip install --quiet --upgrade pip
pip install --quiet PyQt5

# Launch the native GUI
echo ""
echo "✅ Starting application..."
echo ""
python3 gui/wp-sync-native.py
