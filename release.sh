#!/bin/bash
#
# Release script for Webmix Sync Starter
# Automates version updates and distribution package creation
#

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo "======================================"
echo "Webmix Sync Starter - Release Builder"
echo "======================================"
echo ""

# Get current version from setup.py
CURRENT_VERSION=$(grep "CFBundleVersion" setup.py | head -1 | sed "s/.*'\(.*\)'.*/\1/")
echo -e "${BLUE}Current version: ${CURRENT_VERSION}${NC}"
echo ""

# Ask for new version
echo "Enter new version number (e.g., 1.0.1):"
read -r NEW_VERSION

if [[ -z "$NEW_VERSION" ]]; then
    echo -e "${RED}Error: Version number required${NC}"
    exit 1
fi

# Validate version format (basic check)
if ! [[ "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${RED}Error: Version must be in format X.Y.Z (e.g., 1.0.1)${NC}"
    exit 1
fi

# Confirm
echo ""
echo -e "${YELLOW}Ready to release version ${NEW_VERSION}${NC}"
echo "This will:"
echo "  1. Update version in setup.py"
echo "  2. Clean and rebuild the app"
echo "  3. Create DMG installer"
echo "  4. Rename DMG with version number"
echo ""
echo "Continue? (y/n)"
read -r CONFIRM

if [[ "$CONFIRM" != "y" ]]; then
    echo "Cancelled."
    exit 0
fi

# Update version in setup.py
echo ""
echo "📝 Updating version in setup.py..."
sed -i.bak "s/'CFBundleVersion': '.*'/'CFBundleVersion': '$NEW_VERSION'/g" setup.py
sed -i.bak "s/'CFBundleShortVersionString': '.*'/'CFBundleShortVersionString': '$NEW_VERSION'/g" setup.py
rm setup.py.bak
echo -e "${GREEN}✓ Version updated to ${NEW_VERSION}${NC}"

# Clean previous builds
echo ""
echo "🧹 Cleaning previous builds..."
rm -rf build dist
echo -e "${GREEN}✓ Cleaned${NC}"

# Build app
echo ""
echo "🔨 Building application..."
./build-app.sh
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi

# Create DMG
echo ""
echo "📀 Creating DMG installer..."
./create-dmg.sh
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ DMG creation failed${NC}"
    exit 1
fi

# Rename DMG with version
echo ""
echo "📦 Renaming DMG with version..."
DMG_VERSIONED="Webmix-Sync-Starter-v${NEW_VERSION}.dmg"
mv "dist/Webmix-Sync-Starter-Installer.dmg" "dist/${DMG_VERSIONED}"
echo -e "${GREEN}✓ Created: dist/${DMG_VERSIONED}${NC}"

# Calculate size and checksum
DMG_SIZE=$(du -sh "dist/${DMG_VERSIONED}" | cut -f1)
DMG_SHA256=$(shasum -a 256 "dist/${DMG_VERSIONED}" | cut -d' ' -f1)

# Summary
echo ""
echo "======================================"
echo -e "${GREEN}✅ Release ${NEW_VERSION} Complete!${NC}"
echo "======================================"
echo ""
echo "📦 Package: dist/${DMG_VERSIONED}"
echo "💾 Size: ${DMG_SIZE}"
echo "🔐 SHA-256: ${DMG_SHA256}"
echo ""
echo "Next steps:"
echo "  1. Test the DMG: open 'dist/${DMG_VERSIONED}'"
echo "  2. Update CHANGELOG.md with changes"
echo "  3. Commit version changes: git commit -am 'Release v${NEW_VERSION}'"
echo "  4. Create git tag: git tag v${NEW_VERSION}"
echo "  5. Copy DMG to shared location or send to colleagues"
echo ""
echo "Distribution message template:"
echo "----------------------------------------"
echo "Webmix Sync Starter v${NEW_VERSION} is ready!"
echo ""
echo "Download: dist/${DMG_VERSIONED}"
echo "Size: ${DMG_SIZE}"
echo ""
echo "What's new:"
echo "  - [Add your changes here]"
echo ""
echo "Installation: Replace existing app in Applications folder"
echo "----------------------------------------"
