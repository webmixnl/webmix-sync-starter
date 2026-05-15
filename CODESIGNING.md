# Code Signing for macOS Distribution

## The Problem

When distributing the app to colleagues, macOS Gatekeeper blocks it with:
> "Apple could not verify 'Webmix Sync Starter.app' is free of malware"

This happens because the app is not signed with an Apple Developer certificate.

## Solutions

### Option 1: For End Users (Bypass Gatekeeper)

**Method A: Command Line (Recommended)**
```bash
sudo xattr -rd com.apple.quarantine "/Applications/Webmix Sync Starter.app"
```

**Method B: GUI**
1. Right-click the app in Finder
2. Select "Open" (not double-click)
3. Click "Open" in the security warning dialog
4. The app will now open normally in the future

### Option 2: Ad-hoc Code Signing (For Developer)

Sign the app locally after building (doesn't require Apple Developer account):

```bash
codesign --force --deep --sign - "dist/Webmix Sync Starter.app"
```

Add this to your build process in `build-app.sh`:
```bash
# After building, add this line:
codesign --force --deep --sign - "dist/Webmix Sync Starter.app"
```

**Note:** Ad-hoc signing helps but doesn't fully solve Gatekeeper issues. Users may still need to bypass Gatekeeper on first launch.

### Option 3: Apple Developer Certificate (Production)

For professional distribution without security warnings:

1. **Join Apple Developer Program** ($99/year)
   - https://developer.apple.com/programs/

2. **Get Developer ID Application Certificate**
   - Open Xcode → Preferences → Accounts
   - Add your Apple ID
   - Manage Certificates → "+" → Developer ID Application

3. **Sign the app**
   ```bash
   codesign --force --deep --sign "Developer ID Application: Your Name (TEAM_ID)" \
     --options runtime \
     "dist/Webmix Sync Tool.app"
   ```

4. **Notarize the app** (Required for macOS 10.15+)
   ```bash
   # Create a ZIP
   ditto -c -k --keepParent "dist/Webmix Sync Starter.app" "Webmix-Sync-Starter.zip"
   
   # Submit for notarization
   xcrun notarytool submit "Webmix-Sync-Starter.zip" \
     --apple-id "your-email@example.com" \
     --team-id "TEAM_ID" \
     --password "app-specific-password" \
     --wait
   
   # Staple the notarization
   xcrun stapler staple "dist/Webmix Sync Starter.app"
   ```

5. **Update build-app.sh**
   Add signing to the build script:
   ```bash
   echo "🔐 Signing application..."
   codesign --force --deep --sign "Developer ID Application: Your Name (TEAM_ID)" \
     --options runtime \
     "dist/Webmix Sync Starter.app"
   
   if [ $? -eq 0 ]; then
       echo "✓ App signed successfully"
   else
       echo "⚠️  Signing failed - app will require Gatekeeper bypass"
   fi
   ```

## Distribution Instructions for Colleagues

Include these instructions with the DMG:

### Installation Instructions

1. **Download** `Webmix-Sync-Starter-vX.X.X.dmg`
2. **Open** the DMG file
3. **Drag** the app to Applications folder
4. **Important:** Before opening, run this command in Terminal:
   ```bash
   sudo xattr -rd com.apple.quarantine "/Applications/Webmix Sync Starter.app"
   ```
5. **Open** the app from Applications folder

**Alternative:** Right-click the app → "Open" → Click "Open" in the warning dialog

### First Launch
The app will ask for your WordPress credentials and create its settings in:
`~/Library/Application Support/Webmix Sync Starter/`

Your settings will persist across app updates.

## Recommended Approach

**For internal team distribution:**
- Use Option 1 (Gatekeeper bypass) + clear instructions in README
- Or use Option 2 (ad-hoc signing) as a courtesy

**For external/client distribution:**
- Use Option 3 (proper code signing + notarization)
- Required for professional distribution
- Provides the best user experience

## Current Status

✅ App builds successfully
✅ Settings persist across updates
⚠️  Not code-signed (requires Gatekeeper bypass or Apple Developer account)

## See Also

- [Apple Developer Documentation - Code Signing](https://developer.apple.com/support/code-signing/)
- [Apple Developer Documentation - Notarizing macOS Software](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
