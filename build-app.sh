#!/bin/bash
#
# Build script for Webmix Sync Starter
# Creates a standalone macOS application bundle
#

set -e  # Exit on error

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

# Check if venv exists
if [ ! -d "gui/venv" ]; then
    echo "📦 Creating virtual environment..."
    cd gui
    python3 -m venv venv
    cd ..
    echo ""
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source gui/venv/bin/activate
echo ""

# Install/upgrade dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip --quiet
pip install -r gui/requirements.txt --quiet
pip install py2app --quiet
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
python setup.py py2app --quiet 2>&1 | grep -v "copying" || true
echo ""

# Restore setup.py if we modified it
if [ -f "setup.py.bak" ]; then
    mv setup.py.bak setup.py
fi

# Check if build succeeded
if [ -d "dist/Webmix Sync Starter.app" ]; then
    echo -e "${GREEN}✅ Build successful!${NC}"
    echo ""
    
    # Ad-hoc code signing (doesn't remove Gatekeeper warning but helps)
    echo "🔐 Ad-hoc signing application..."
    codesign --force --deep --sign - "dist/Webmix Sync Starter.app" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ App signed (ad-hoc)${NC}"
    else
        echo -e "${YELLOW}⚠️  Ad-hoc signing failed (not critical)${NC}"
    fi
    echo ""
    
    echo "Application built at:"
    echo "  dist/Webmix Sync Starter.app"
    echo ""
    APP_SIZE=$(du -sh "dist/Webmix Sync Starter.app" | cut -f1)
    echo "Size: $APP_SIZE"
    echo ""
    echo -e "${YELLOW}⚠️  Note: App is not notarized - users will need to bypass Gatekeeper${NC}"
    echo "See CODESIGNING.md and INSTALLATION.md for instructions"
    echo ""
    echo "Next steps:"
    echo "  • Test: open 'dist/Webmix Sync Starter.app'"
    echo "  • Create DMG: ./create-dmg.sh"
    echo "  • For production: Sign with Developer ID (see CODESIGNING.md)"
else
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi

# Deactivate venv
deactivate
