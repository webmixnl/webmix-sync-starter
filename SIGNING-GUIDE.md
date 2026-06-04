# Quick Signing & Distribution Guide

## One-Time Setup (First Time Only)

### 1. Get App-Specific Password

1. Go to https://appleid.apple.com/account/manage
2. Sign in with `bram@webmix.nl`
3. Security → App-Specific Passwords → Generate Password
4. Name it "Webmix Notarization"
5. Save the password (you'll paste it in step 3)

### 2. Build & Sign Your First App

```bash
./build-app.sh
```

When prompted "Sign and notarize now?", press **y**

### 3. Enter Credentials (First Time Only)

The script will ask for your app-specific password.
Paste the password from step 1.

This is stored securely in your keychain - you only do this once!

---

## Regular Workflow (After First Setup)

### Build, Sign, and Distribute

```bash
# 1. Build and sign the app
./build-app.sh
# Press 'y' when asked to sign

# 2. Create a signed DMG
./create-dmg.sh

# 3. Distribute the DMG!
# Share: dist/Webmix-Sync-Starter-Installer.dmg
```

### Alternative: Sign Existing Build

If you already built the app and want to sign it:

```bash
./sign-and-notarize.sh
```

---

## What Your Colleagues Get

When you share the signed DMG:

✅ **No security warnings**  
✅ **No terminal commands needed**  
✅ **Professional installation experience**  

They just:
1. Download the DMG
2. Drag to Applications
3. Launch the app immediately

---

## Timing

- **Build**: 2-5 minutes
- **Signing**: 5 seconds
- **Notarization**: 2-5 minutes (Apple's servers)
- **DMG Creation**: 10 seconds

**Total**: ~5-10 minutes per release

---

## Troubleshooting

### Check Your Certificate

```bash
security find-identity -v -p codesigning
```

Should show: `Developer ID Application: webmix B.V. (P6P2GY673G)`

### Reset Notarization Credentials

```bash
xcrun notarytool store-credentials webmix-notarization \
  --apple-id bram@webmix.nl \
  --team-id P6P2GY673G
```

### Get Notarization Logs

If notarization fails:
```bash
xcrun notarytool log <submission-id> --keychain-profile webmix-notarization
```

The submission ID is shown in the failed notarization output.

---

## File Overview

| Script | Purpose |
|--------|---------|
| `build-app.sh` | Build the app bundle |
| `sign-and-notarize.sh` | Sign and notarize with Apple |
| `create-dmg.sh` | Create installer DMG |
| `release.sh` | All-in-one release script |

---

## Quick Commands

```bash
# Full release process
./build-app.sh && ./create-dmg.sh

# Just sign existing app
./sign-and-notarize.sh

# Create DMG from signed app
./create-dmg.sh

# Test the app locally
open "dist/Webmix Sync Starter.app"

# Check if app is signed
codesign --verify --deep --strict "dist/Webmix Sync Starter.app"

# Check if app is notarized
xcrun stapler validate "dist/Webmix Sync Starter.app"
```

---

## Security Notes

- Your app-specific password is stored in macOS Keychain (encrypted)
- Never share your app-specific password
- Your Developer ID certificate is in your Keychain Access
- Notarization happens on Apple's servers (they scan for malware)
- The notarization ticket is "stapled" to your app for offline verification

---

For detailed information, see:
- [CODESIGNING.md](CODESIGNING.md) - Complete signing documentation
- [DISTRIBUTION.md](DISTRIBUTION.md) - Distribution checklist
- [BUILD.md](BUILD.md) - Build process details
