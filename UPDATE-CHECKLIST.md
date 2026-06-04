# Auto-Update Setup Checklist

## ✅ What's Been Set Up

Your app now has a complete auto-update system! Here's what was added:

### 1. Update Checker Module (`gui/update_checker.py`)
- Checks GitHub Releases API for new versions
- Downloads and installs updates
- Handles version comparison

### 2. GUI Integration (`gui/wp-sync-native.py`)
- "Help" menu with "Check for Updates" option
- "About" menu showing current version
- Progress dialogs for download/install
- User-friendly update notifications

### 3. Release Automation (`release.sh`)
- Automatically creates GitHub Releases
- Uploads signed DMG to GitHub
- Creates git tags and pushes to repo
- Generates release notes

### 4. Dependencies
- Added `packaging` library for version comparison
- Updated `requirements.txt` and `setup.py`

---

## 🚀 Quick Start Guide

### Step 1: Configure Your GitHub Repository

Edit `gui/wp-sync-native.py` (lines 8-9):

```python
GITHUB_REPO_OWNER = "webmix"  # ← Change to YOUR GitHub username/org
GITHUB_REPO_NAME = "webmix-sync-starter"  # ← Change to YOUR repo name
```

### Step 2: Install GitHub CLI (One-Time)

```bash
brew install gh
gh auth login
```

Follow the prompts to authenticate.

### Step 3: Test the Update System

First, let's rebuild the app with the new update checker:

```bash
# Clean build
rm -rf build dist gui/venv

# Build with signing (press 'y' when asked)
./build-app.sh

# Test the app
open "dist/Webmix Sync Starter.app"
```

Check the "Help" menu - you should see:
- "Check for Updates..."
- "About Webmix Sync Starter v1.0.10"

### Step 4: Create Your First Release

```bash
./release.sh
```

When prompted:
1. Enter new version: `1.0.11` (or your desired version)
2. Confirm: `y`
3. Wait for build to complete
4. Create GitHub Release: `y`
5. Enter release notes (or press Ctrl+D for default)

The script will:
- ✅ Build and sign your app
- ✅ Create DMG
- ✅ Push to GitHub
- ✅ Create GitHub Release
- ✅ Upload DMG to release

---

## 📋 Testing Checklist

After creating your first release, test the update system:

### On Your Machine (Developer Testing)

1. **Check Current Version**
   ```bash
   open "dist/Webmix Sync Starter.app"
   # Click Help → About
   # Verify version shows correctly
   ```

2. **Test Update Check**
   - Click `Help` → `Check for Updates`
   - Should say "You have the latest version"

3. **Test Update with Older Version**
   - Edit `gui/wp-sync-native.py`: Change `APP_VERSION = "1.0.9"`
   - Rebuild: `./build-app.sh`
   - Open app and check for updates
   - Should offer to download v1.0.11 (or your latest)

### For Your Team (User Testing)

1. **Share Release URL**
   - Go to: `https://github.com/YOUR_USERNAME/YOUR_REPO/releases`
   - Copy the release URL
   - Share with your team

2. **They Install**
   - Download the DMG from GitHub Releases
   - Install the app
   - Launch it

3. **They Check for Updates**
   - Help → Check for Updates
   - Should say "You have the latest version"

4. **When You Release Next Update**
   - They check for updates
   - See notification about new version
   - Can install with one click

---

## 🔄 Release Workflow (Going Forward)

### Every Time You Release:

```bash
# 1. Make your changes to the code
# 2. Test thoroughly
# 3. Run the release script
./release.sh

# That's it! Your team gets notified automatically.
```

### Version Numbering Guide:

- **Bug fixes**: `1.0.10` → `1.0.11` (patch)
- **New features**: `1.0.11` → `1.1.0` (minor)
- **Breaking changes**: `1.1.0` → `2.0.0` (major)

---

## 🎯 What Your Users Experience

### First Install
1. Download DMG from your GitHub Releases page
2. Install the app
3. Use normally

### When Update Available
1. Open app
2. Click "Help" → "Check for Updates"
3. See "New version available!" dialog
4. Click "Yes" to download
5. DMG downloads and opens
6. Drag to Applications (replaces old version)
7. Relaunch app

**No terminal commands! No manual downloads!**

---

## 🛠️ Troubleshooting

### Build Errors

If build fails, ensure:
```bash
# Install/update dependencies
rm -rf gui/venv
./build-app.sh
```

### GitHub CLI Issues

```bash
# Check if logged in
gh auth status

# Re-login if needed
gh auth login

# Check repo access
gh repo view
```

### Update Check Not Working

Ensure in `gui/wp-sync-native.py`:
- `GITHUB_REPO_OWNER` is correct
- `GITHUB_REPO_NAME` is correct
- Repository is **public** (or users have access)

---

## 📚 Documentation

- **[AUTO-UPDATE.md](AUTO-UPDATE.md)** - Complete auto-update documentation
- **[SIGNING-GUIDE.md](SIGNING-GUIDE.md)** - Code signing guide
- **[DISTRIBUTION.md](DISTRIBUTION.md)** - Distribution checklist

---

## ✨ Summary

You now have:

- ✅ **Automatic update checking** in your app
- ✅ **One-click updates** for users
- ✅ **Automated releases** with GitHub
- ✅ **Proper versioning** and code signing
- ✅ **Professional distribution** workflow

Your team will always have the latest version with minimal effort!

---

## Next Steps

1. Update `GITHUB_REPO_OWNER` and `GITHUB_REPO_NAME` in `gui/wp-sync-native.py`
2. Run `./release.sh` to create your first release
3. Share the GitHub Releases URL with your team
4. From now on, just run `./release.sh` whenever you want to push an update!

**Questions?** Check [AUTO-UPDATE.md](AUTO-UPDATE.md) for detailed documentation.
