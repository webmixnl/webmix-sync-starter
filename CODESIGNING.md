# Code Signing for macOS Distribution

## ✅ Current Setup

Your app is now configured for **proper code signing and notarization** with your Apple Developer certificate:

- **Certificate**: Developer ID Application: webmix B.V. (P6P2GY673G)
- **Team ID**: P6P2GY673G
- **Apple ID**: bram@webmix.nl

## Quick Start

### Build and Sign Your App

1. **Build the app**:
   ```bash
   ./build-app.sh
   ```
   - The build script will ask if you want to sign and notarize
   - Answer 'y' to proceed with signing

2. **Or sign separately** (if you already built the app):
   ```bash
   ./sign-and-notarize.sh
   ```

3. **Create a signed DMG**:
   ```bash
   ./create-dmg.sh
   ```

### First Time Setup

The first time you run `sign-and-notarize.sh`, you'll need an **app-specific password**:

1. Go to https://appleid.apple.com/account/manage
2. Sign in with your Apple ID (bram@webmix.nl)
3. Under "Security" → "App-Specific Passwords"
4. Click "Generate Password"
5. Name it "Webmix Notarization"
6. Copy the generated password
7. Paste it when the script prompts you

The password is stored securely in your macOS keychain and only needs to be entered once.

## Distribution

Once your app is signed and notarized, share the DMG:

**✅ What your colleagues get:**
- Double-click to install
- Drag to Applications
- Launch immediately
- **No security warnings**
- **No terminal commands needed**

## How It Works

The signing process:

1. **Code Signing**: Signs the app bundle with your Developer ID certificate
2. **Hardened Runtime**: Enables security protections required by Apple
3. **Notarization**: Submits the app to Apple for automated malware scanning
4. **Stapling**: Attaches the notarization ticket to the app (works offline)

This entire process is automated by `sign-and-notarize.sh`.

## Troubleshooting

### "No valid signing identities found"

Your Developer ID certificate may have expired or is not installed.

**Check certificate**:
```bash
security find-identity -v -p codesigning
```

You should see: `Developer ID Application: webmix B.V. (P6P2GY673G)`

**If missing**:
1. Open Xcode → Settings → Accounts
2. Add your Apple ID if not present
3. Select your team → Manage Certificates
4. Click + → Developer ID Application

### "Invalid credentials"

Your app-specific password may be incorrect or expired.

**Reset credentials**:
```bash
xcrun notarytool store-credentials webmix-notarization \
  --apple-id bram@webmix.nl \
  --team-id P6P2GY673G
```

Then enter your app-specific password when prompted.

### "Notarization failed"

Get detailed error logs:
```bash
# After a failed notarization, the script will show a submission ID
xcrun notarytool log <submission-id> --keychain-profile webmix-notarization
```

Common issues:
- **Unsigned dependencies**: All embedded frameworks must be signed
- **Invalid entitlements**: Check hardened runtime requirements
- **Timeout**: Notarization can take 5-15 minutes during peak times

## Alternative: Manual Distribution (Not Recommended)

If you need to distribute an unsigned app (for quick testing only):

1. Build without signing
2. Provide this command to users:
   ```bash
   sudo xattr -rd com.apple.quarantine "/Applications/Webmix Sync Starter.app"
   ```

**Note**: This requires sudo access and is not user-friendly. Use proper signing for any real distribution.

## See Also

- [Apple Developer Documentation - Code Signing](https://developer.apple.com/support/code-signing/)
- [Apple Developer Documentation - Notarizing macOS Software](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [Distribution Guide](DISTRIBUTION.md)
