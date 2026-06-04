# Auto-Update System

Your app now has automatic update checking integrated with GitHub Releases!

## How It Works

1. **Version Checking**: The app checks GitHub Releases for new versions
2. **Update Notification**: Users are notified when updates are available
3. **One-Click Install**: Users can download and install updates from within the app
4. **Automatic Distribution**: Each release you create is automatically available to all users

## For You (Developer)

### Initial Setup

1. **Configure GitHub Repository** in `gui/wp-sync-native.py`:
   ```python
   GITHUB_REPO_OWNER = "webmix"  # Change to your GitHub username/org
   GITHUB_REPO_NAME = "webmix-sync-starter"  # Change to your repo name
   ```

2. **Install GitHub CLI** (if not already installed):
   ```bash
   brew install gh
   gh auth login
   ```

### Creating a Release

When you're ready to release a new version:

```bash
./release.sh
```

The script will:
1. Ask for the new version number (e.g., `1.0.11`)
2. Update version in `setup.py` and `gui/wp-sync-native.py`
3. Build and sign the app
4. Create a signed DMG
5. **Automatically create a GitHub Release** with the DMG attached
6. Push changes and tags to GitHub

That's it! All existing installations will now be notified of the update.

### Release Workflow

```bash
# Start the release process
./release.sh

# Enter new version: 1.0.11
# Confirm: y
# Create GitHub Release: y
# Enter release notes (or press Ctrl+D for default)

# Done! ✅
```

### Manual Release (Alternative)

If you prefer manual control:

```bash
# Build the app
./build-app.sh

# Create DMG
./create-dmg.sh

# Create GitHub release manually
gh release create v1.0.11 \
  dist/Webmix-Sync-Starter-v1.0.11.dmg \
  --title "Webmix Sync Starter v1.0.11" \
  --notes "Release notes here"
```

## For Your Users

### Checking for Updates

Users can check for updates in two ways:

1. **Manual Check**: `Help` → `Check for Updates...`
2. **Automatic (Optional)**: You can add automatic checking on app startup

### Update Process

When an update is available:

1. User clicks "Help" → "Check for Updates"
2. Dialog shows new version and release notes
3. User clicks "Yes" to download
4. DMG downloads and opens automatically
5. User drags app to Applications (replaces old version)
6. User relaunches the app

✨ **No terminal commands needed!**

## Version Management

### Version Numbers

Follow semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes (1.0.0 → 2.0.0)
- **MINOR**: New features (1.0.0 → 1.1.0)
- **PATCH**: Bug fixes (1.0.0 → 1.0.1)

### Keeping Versions in Sync

The release script automatically updates:
- `setup.py`: `CFBundleVersion` and `CFBundleShortVersionString`
- Git tag: `v1.0.11`
- GitHub Release: `v1.0.11`

**Important**: Always use `release.sh` to maintain version consistency.

## Troubleshooting

### "GitHub CLI not installed"

```bash
brew install gh
gh auth login
```

### "Not logged in to GitHub"

```bash
gh auth login
# Follow the prompts
```

### "Push failed"

Make sure you have:
- Committed all changes
- Set up your GitHub remote: `git remote -v`
- Proper permissions to push to the repo

### Update Check Fails for Users

Users need internet connection to check for updates. The app will show a friendly error message if:
- No internet connection
- GitHub is unreachable
- Repository is private (update checker requires public repo)

## Best Practices

1. **Test Before Release**: Always test the DMG on a clean machine before releasing
2. **Write Release Notes**: Users appreciate knowing what changed
3. **Update CHANGELOG.md**: Keep a changelog for reference
4. **Semantic Versioning**: Follow semver for predictable updates
5. **Sign Your Releases**: Always code sign and notarize (already configured!)

## Advanced: Automatic Update Checks

To automatically check for updates on app startup, add this to `WPSyncGUI.__init__`:

```python
# Check for updates on startup (silent check)
if UPDATE_CHECKER_AVAILABLE:
    QTimer.singleShot(3000, lambda: self.check_for_updates(silent=True))
```

This checks for updates 3 seconds after launch without interrupting the user.

## Files Modified for Auto-Update

- `gui/update_checker.py` - Update checking logic
- `gui/wp-sync-native.py` - UI integration
- `gui/requirements.txt` - Added `packaging` dependency
- `setup.py` - Added `packaging` package
- `release.sh` - GitHub Release automation

## Example Release Flow

```bash
# You make some changes and want to release
./release.sh

# Output:
# Current version: 1.0.10
# Enter new version: 1.0.11
# 
# Ready to release version 1.0.11
# Continue? (y/n) y
#
# ✅ Build successful!
# ✅ DMG created successfully!
# 
# Create GitHub Release? [Y/n] y
# Enter release notes (Ctrl+D when done):
# - Fixed SSH connection timeout
# - Added better error messages
# - Performance improvements
# ^D
#
# 🎉 GitHub Release created successfully!
# 🌐 View release: https://github.com/webmix/webmix-sync-starter/releases/tag/v1.0.11
# 🎉 Your app will now auto-update from GitHub!
```

Users with v1.0.10 or earlier will see an update notification next time they check!

## Security Notes

- Updates are downloaded from your GitHub Releases (HTTPS)
- The DMG is code-signed and notarized by Apple
- Users verify the signature automatically when they install
- No credentials are stored or transmitted during updates

## Support

If users have issues updating:
1. They can always download manually from GitHub Releases
2. Old versions continue to work (backward compatible)
3. They can check the release page: `https://github.com/YOUR_USERNAME/YOUR_REPO/releases`
