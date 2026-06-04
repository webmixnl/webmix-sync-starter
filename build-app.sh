#!/bin/bash
#
# Build script for Webmix Sync Starter
# Creates a standalone macOS application bundle
#

set -e  # Exit on error

# Clear any Python environment variables that might interfere
# (from previously installed py2app applications)
unset PYTHONHOME PYTHONPATH

# Use Python 3.12 (more stable than 3.14)
PYTHON_CMD="python3.12"

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo "======================================"
echo "Building Webmix Sync Starter"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist
echo ""

# Check if venv exists and is valid
VENV_DIR="gui/venv"
PYTHON_BIN="$VENV_DIR/bin/python3"
PIP_BIN="$VENV_DIR/bin/pip"

# Check if venv needs to be recreated (invalid or moved location)
VENV_VALID=true
if [ ! -d "$VENV_DIR" ]; then
    VENV_VALID=false
elif [ ! -f "$PYTHON_BIN" ]; then
    VENV_VALID=false
else
    # Test if pip works (it has hardcoded paths that break when venv is moved)
    "$PIP_BIN" --version &>/dev/null || VENV_VALID=false
fi

if [ "$VENV_VALID" = false ]; then
    echo "📦 Creating/recreating virtual environment..."
    rm -rf "$VENV_DIR"
    "$PYTHON_CMD" -m venv "$VENV_DIR"
    echo ""
fi

# Verify venv is working
if [ ! -f "$PYTHON_BIN" ]; then
    echo -e "${RED}❌ Error: Virtual environment not properly created${NC}"
    exit 1
fi

echo "🔌 Using virtual environment..."
echo ""

# Install/upgrade dependencies
echo "📥 Installing dependencies..."
"$PIP_BIN" install --upgrade pip --quiet
"$PIP_BIN" install -r gui/requirements.txt --quiet
"$PIP_BIN" install py2app --quiet
echo ""

# Check for app icon
if [ ! -f "gui/app-icon.icns" ]; then
    echo -e "${YELLOW}⚠️  Warning: gui/app-icon.icns not found${NC}"
    echo "The app will build with the default Python icon."
    echo ""
    echo "To create an icon from your PNG:"
    echo "  1. Create iconset: mkdir icon.iconset"
    echo "  2. Resize PNG to 1024x1024"
    echo "  3. Generate sizes: sips -z 512 512 wp-sync-starter-logo.png --out icon.iconset/icon_512x512.png"
    echo "  4. Convert: iconutil -c icns icon.iconset -o gui/app-icon.icns"
    echo ""
    
    # Comment out iconfile in setup.py temporarily
    if grep -q "'iconfile':" setup.py; then
        echo "Temporarily disabling iconfile in setup.py..."
        sed -i.bak "s/'iconfile':.*$/'iconfile': None,  # Icon not found/" setup.py
    fi
fi

# Build the app
echo "🔨 Building application (this may take a few minutes)..."
"$PYTHON_BIN" setup.py py2app --quiet 2>&1 | grep -v "copying" || true
echo ""

# Restore setup.py if we modified it
if [ -f "setup.py.bak" ]; then
    mv setup.py.bak setup.py
fi

# Check if build succeeded
if [ -d "dist/Webmix Sync Starter.app" ]; then
    echo -e "${GREEN}✅ Build successful!${NC}"
    echo ""
    
    echo "Application built at:"
    echo "  dist/Webmix Sync Starter.app"
    echo ""
    APP_SIZE=$(du -sh "dist/Webmix Sync Starter.app" | cut -f1)
    echo "Size: $APP_SIZE"
    echo ""
    
    # Offer to sign and notarize
    echo -e "${BLUE}Would you like to sign and notarize the app for distribution?${NC}"
    echo "(Requires Apple Developer ID certificate)"
    echo ""
    read -p "Sign and notarize now? [y/N]: " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        ./sign-and-notarize.sh
    else
        echo ""
        echo "Skipping code signing."
        echo ""
        echo -e "${YELLOW}⚠️  Note: App is not signed/notarized${NC}"
        echo "Users will need to bypass Gatekeeper on first launch."
        echo ""
        echo "To sign later, run: ./sign-and-notarize.sh"
        echo ""
    fi
    
    echo "Next steps:"
    echo "  • Test: open 'dist/Webmix Sync Starter.app'"
    echo "  • Create DMG: ./create-dmg.sh"
else
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi
