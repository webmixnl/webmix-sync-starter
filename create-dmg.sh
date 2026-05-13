#!/bin/bash
#
# Create a DMG installer for Webmix Sync Starter
# Requires: create-dmg (brew install create-dmg)
#

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

APP_NAME="Webmix Sync Starter"
DMG_NAME="Webmix-Sync-Starter-Installer"
VERSION="1.0.0"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "======================================"
echo "Creating DMG Installer"
echo "======================================"
echo ""

# Check if app exists
if [ ! -d "dist/$APP_NAME.app" ]; then
    echo -e "${RED}❌ Error: Application not found${NC}"
    echo "Please build the app first: ./build-app.sh"
    exit 1
fi

# Check if create-dmg is installed
if ! command -v create-dmg &> /dev/null; then
    echo -e "${YELLOW}⚠️  create-dmg not found${NC}"
    echo ""
    echo "Installing create-dmg..."
    brew install create-dmg
    echo ""
fi

# Remove old DMG if exists
rm -f "dist/${DMG_NAME}.dmg"

# Create DMG
echo "📀 Creating DMG installer..."

# Build create-dmg command with optional icon
DMG_ARGS=(
  --volname "$APP_NAME"
  --window-pos 200 120
  --window-size 800 400
  --icon-size 100
  --icon "$APP_NAME.app" 200 190
  --hide-extension "$APP_NAME.app"
  --app-drop-link 600 185
)

# Add volume icon if it exists
if [ -f "gui/app-icon.icns" ]; then
    DMG_ARGS+=(--volicon "gui/app-icon.icns")
else
    echo -e "${YELLOW}Note: No icon file found (gui/app-icon.icns)${NC}"
    echo "DMG will use default icon."
    echo ""
fi

create-dmg "${DMG_ARGS[@]}" \
  "dist/${DMG_NAME}.dmg" \
  "dist/$APP_NAME.app" 2>&1 | grep -v "hdiutil" || true

echo ""

# Check if DMG was created
if [ -f "dist/${DMG_NAME}.dmg" ]; then
    DMG_SIZE=$(du -sh "dist/${DMG_NAME}.dmg" | cut -f1)
    echo -e "${GREEN}✅ DMG created successfully!${NC}"
    echo ""
    echo "Installer: dist/${DMG_NAME}.dmg"
    echo "Size: $DMG_SIZE"
    echo ""
    echo "Distribution instructions:"
    echo "  1. Share the DMG file with colleagues"
    echo "  2. They double-click to mount it"
    echo "  3. They drag the app to Applications folder"
    echo "  4. Done!"
else
    echo -e "${RED}❌ DMG creation failed${NC}"
    echo ""
    echo "Alternative: Create a ZIP file"
    echo "  cd dist && zip -r '${APP_NAME}.zip' '${APP_NAME}.app'"
    exit 1
fi
