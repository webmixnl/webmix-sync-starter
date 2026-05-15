# Distribution Checklist

Quick reference for building and distributing Webmix Sync Tool to colleagues.

## Build Process

### 1. Build the Application

```bash
./build-app.sh
```

**Output:** `dist/Webmix Sync Tool.app` (~170MB)

### 2. Test the Application

```bash
open "dist/Webmix Sync Tool.app"
```

Verify:
- ✅ App launches without errors
- ✅ Settings can be opened
- ✅ Sites can be loaded/created
- ✅ Pull/Push commands work
- ✅ Watch mode functions
- ✅ SSH terminal opens

### 3. Create Installer (Optional but Recommended)

```bash
./create-dmg.sh
```

**Output:** `dist/Webmix-Sync-Starter-Installer.dmg` (~100MB compressed)

## Distribution Options

### Option A: DMG Installer (Recommended)

Share: `dist/Webmix-Sync-Starter-Installer.dmg`

**User steps:**
1. Double-click DMG to mount
2. Drag app to Applications folder
3. Eject DMG
4. Install dependencies: `brew install fswatch rsync`
5. Launch from Applications

### Option B: ZIP Archive

```bash
cd dist
zip -r "Webmix Sync Tool.zip" "Webmix Sync Tool.app"
```

Share: `dist/Webmix Sync Tool.zip`

**User steps:**
1. Unzip the file
2. Drag app to Applications folder
3. Install dependencies: `brew install fswatch rsync`
4. Launch from Applications

### Option C: Direct App (Quick Test)

Share: `dist/Webmix Sync Tool.app` (as folder)

**Note:** macOS may show security warnings when copying folders directly.
DMG or ZIP is preferred for proper distribution.

## User Requirements

End users need these tools installed:

```bash
brew install fswatch rsync
```

**Note:** They also need:
- macOS 10.13 or later
- SSH key authentication set up for their servers
- WordPress credentials (username + application password)

## First-Time Setup for Users

1. **Install the app** (via DMG or ZIP)
2. **Install dependencies:**
   ```bash
   brew install fswatch rsync
   ```
3. **Launch the app**
4. **Configure WordPress credentials:**
   - Menu: Settings → Preferences
   - Enter WordPress URL, username, and application password
   - Click "Test Authentication"
5. **Sync sites from API:**
   - Click "Sync from API"
   - Select sites to configure
   - Set SSH details and local paths
6. **Start syncing!**

## Troubleshooting for Users

### "Cannot open app because it's from an unidentified developer"

**Solution:**
```bash
xattr -cr "/Applications/Webmix Sync Tool.app"
```

Or: Right-click app → Open → Confirm

### "fswatch command not found"

**Solution:**
```bash
brew install fswatch rsync
```

### SSH connection fails

**Check:**
- SSH key exists: `ls ~/.ssh/id_rsa`
- SSH key is added to remote server
- SSH port is correct (usually 22)
- Can connect manually: `ssh user@host`

### Watch mode not detecting changes

**Check:**
- fswatch is installed: `which fswatch`
- Local folder exists and has write permissions
- Sync items are correctly configured

## Build Troubleshooting

### Build fails with "No module named PyQt5"

```bash
source gui/venv/bin/activate
pip install -r gui/requirements.txt
python setup.py py2app
```

### App icon missing

Create an ICNS file:
1. Create 1024x1024 PNG icon
2. Convert: `iconutil -c icns icon.iconset`
3. Save as: `gui/app-icon.icns`
4. Rebuild

### App crashes on launch

Check:
- All dependencies in setup.py OPTIONS
- DATA_FILES includes all necessary scripts
- Permissions on bin/ scripts: `chmod +x bin/*`

## Version Updates

When releasing a new version:

1. Update version in `setup.py` (CFBundleVersion)
2. Update version in `create-dmg.sh` (VERSION variable)
3. Clean and rebuild: `rm -rf build dist && ./build-app.sh`
4. Test thoroughly
5. Create DMG: `./create-dmg.sh`
6. Rename DMG to include version: `Webmix-Sync-Starter-v1.0.0.dmg`
7. Distribute

## File Sizes

- Source code: ~1.3MB
- Built app: ~170MB (includes Python + PyQt5)
- DMG installer: ~100MB (compressed)
- ZIP archive: ~110MB (compressed)
