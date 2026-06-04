#!/bin/bash
#
# Sign and notarize Webmix Sync Starter for macOS distribution
# Requires: Apple Developer ID certificate and app-specific password
#

set -e  # Exit on error

# Clear any Python environment variables that might interfere
unset PYTHONHOME PYTHONPATH

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# Configuration
APP_NAME="Webmix Sync Starter"
APP_PATH="dist/$APP_NAME.app"
DEVELOPER_ID="Developer ID Application: webmix B.V. (P6P2GY673G)"
TEAM_ID="P6P2GY673G"
APPLE_ID="bram@webmix.nl"
KEYCHAIN_PROFILE="webmix-notarization"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "======================================"
echo "Code Signing & Notarization"
echo "======================================"
echo ""

# Check if app exists
if [ ! -d "$APP_PATH" ]; then
    echo -e "${RED}❌ Error: Application not found at $APP_PATH${NC}"
    echo "Please build the app first: ./build-app.sh"
    exit 1
fi

# Step 1: Store credentials (only needed once)
echo "🔑 Checking notarization credentials..."
if ! xcrun notarytool store-credentials --list 2>/dev/null | grep -q "$KEYCHAIN_PROFILE"; then
    echo ""
    echo -e "${YELLOW}Credentials not found in keychain.${NC}"
    echo "You'll need your app-specific password from:"
    echo "https://appleid.apple.com/account/manage"
    echo ""
    xcrun notarytool store-credentials "$KEYCHAIN_PROFILE" \
        --apple-id "$APPLE_ID" \
        --team-id "$TEAM_ID"
    echo ""
else
    echo -e "${GREEN}✓ Credentials found${NC}"
    echo ""
fi

# Step 2: Sign the application
echo "🔐 Signing application with hardened runtime..."

# Sign PyQt5 framework binaries (they're inside Versions/5/)
echo "  → Signing PyQt5 frameworks..."
find "$APP_PATH/Contents/Resources/lib/python3.12/PyQt5/Qt5/lib" -name "*.framework" -type d 2>/dev/null | while read framework; do
    # Sign the actual binary inside Versions/5/
    framework_name=$(basename "$framework" .framework)
    if [ -f "$framework/Versions/5/$framework_name" ]; then
        codesign --force --sign "$DEVELOPER_ID" --options runtime --timestamp "$framework/Versions/5/$framework_name" 2>/dev/null || true
    fi
    # Also sign the framework bundle itself
    codesign --force --sign "$DEVELOPER_ID" --options runtime --timestamp "$framework" 2>/dev/null || true
done

# Sign all other frameworks
echo "  → Signing other frameworks..."
find "$APP_PATH/Contents/Frameworks" -name "*.framework" -type d 2>/dev/null | while read framework; do
    codesign --force --sign "$DEVELOPER_ID" --options runtime --timestamp "$framework" 2>/dev/null || true
done

# Sign all dylibs
echo "  → Signing dynamic libraries..."
find "$APP_PATH/Contents" -name "*.dylib" -type f 2>/dev/null | while read dylib; do
    codesign --force --sign "$DEVELOPER_ID" --options runtime --timestamp "$dylib" 2>/dev/null || true
done

# Sign all .so files
find "$APP_PATH/Contents" -name "*.so" -type f 2>/dev/null | while read so; do
    codesign --force --sign "$DEVELOPER_ID" --options runtime --timestamp "$so" 2>/dev/null || true
done

# Sign the Python executable
if [ -f "$APP_PATH/Contents/MacOS/python" ]; then
    echo "  → Signing Python executable..."
    codesign --force --sign "$DEVELOPER_ID" --options runtime --timestamp "$APP_PATH/Contents/MacOS/python"
fi

# Finally, sign the app bundle itself
echo "  → Signing main application bundle..."
codesign --force \
    --sign "$DEVELOPER_ID" \
    --options runtime \
    --timestamp \
    "$APP_PATH"

# Verify signing
if codesign --verify --deep --strict --verbose=2 "$APP_PATH" 2>&1 | grep -q "valid on disk"; then
    echo -e "${GREEN}✓ Application signed successfully${NC}"
    echo ""
else
    echo -e "${RED}❌ Signing verification failed${NC}"
    exit 1
fi

# Step 3: Create ZIP for notarization
echo "📦 Creating archive for notarization..."
ZIP_FILE="dist/$APP_NAME.zip"
rm -f "$ZIP_FILE"
ditto -c -k --keepParent "$APP_PATH" "$ZIP_FILE"
echo -e "${GREEN}✓ Archive created${NC}"
echo ""

# Step 4: Submit for notarization
echo "☁️  Submitting to Apple for notarization..."
echo -e "${BLUE}This may take a few minutes...${NC}"
echo ""

NOTARIZATION_OUTPUT=$(xcrun notarytool submit "$ZIP_FILE" \
    --keychain-profile "$KEYCHAIN_PROFILE" \
    --wait 2>&1)

echo "$NOTARIZATION_OUTPUT"
echo ""

# Check if notarization succeeded
if echo "$NOTARIZATION_OUTPUT" | grep -q "status: Accepted"; then
    echo -e "${GREEN}✓ Notarization successful!${NC}"
    echo ""
    
    # Step 5: Staple the ticket
    echo "📎 Stapling notarization ticket to app..."
    xcrun stapler staple "$APP_PATH"
    
    # Verify stapling
    if xcrun stapler validate "$APP_PATH" 2>&1 | grep -q "The validate action worked"; then
        echo -e "${GREEN}✓ Ticket stapled successfully${NC}"
        echo ""
    else
        echo -e "${YELLOW}⚠️  Stapling verification failed (but notarization succeeded)${NC}"
        echo ""
    fi
    
    # Clean up ZIP
    rm -f "$ZIP_FILE"
    
    echo -e "${GREEN}======================================"
    echo "✅ SUCCESS!"
    echo "======================================${NC}"
    echo ""
    echo "Your app is now signed and notarized!"
    echo ""
    echo "Next steps:"
    echo "  1. Test the app: open '$APP_PATH'"
    echo "  2. Create DMG: ./create-dmg.sh"
    echo "  3. Distribute the DMG to your team"
    echo ""
    echo "Your colleagues can now:"
    echo "  • Install without security warnings"
    echo "  • Run the app immediately after installation"
    echo "  • No terminal commands needed!"
    echo ""
    
else
    echo -e "${RED}❌ Notarization failed${NC}"
    echo ""
    echo "To get more details, run:"
    echo "  xcrun notarytool log <submission-id> --keychain-profile $KEYCHAIN_PROFILE"
    echo ""
    exit 1
fi
