# Update and Release Workflow

This guide explains how to manage versions and distribute updates to colleagues.

## Version Numbering

Use semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR** (1.x.x): Breaking changes, major new features
- **MINOR** (x.1.x): New features, backward compatible
- **PATCH** (x.x.1): Bug fixes, small improvements

Current version: **1.0.0**

## Update Workflow

### 1. Make Your Changes

Edit code, fix bugs, add features as needed.

### 2. Update Version Number

Edit `setup.py` and update both version fields:

```python
'CFBundleVersion': '1.0.1',              # Changed
'CFBundleShortVersionString': '1.0.1',   # Changed
```

### 3. Document Changes

Add notes to `CHANGELOG.md` (or create it):

```markdown
## [1.0.1] - 2026-05-13

### Fixed
- Fixed rsync SSH command quoting issue
- Fixed sync items not loading when editing sites
- Fixed path handling for app bundles with spaces

### Changed
- Improved error messages in pull/push operations
```

### 4. Rebuild and Test

```bash
# Clean rebuild
rm -rf build dist
./build-app.sh

# Test locally
open "dist/Webmix Sync Tool.app"

# Test pull, push, watch, SSH terminal
# Verify all features work
```

### 5. Create Distribution Package

```bash
# Create DMG installer
./create-dmg.sh

# Rename to include version
mv "dist/Webmix-Sync-Starter-Installer.dmg" "dist/Webmix-Sync-Starter-v1.0.1.dmg"
```

### 6. Distribute to Colleagues

**Option A: Shared Drive/Cloud Storage**
```bash
# Copy to shared location
cp "dist/Webmix-Sync-Starter-v1.0.1.dmg" "/path/to/shared/drive/"
```

**Option B: Email/Slack**
- Attach the DMG file
- Include release notes
- Mention it's a required/optional update

**Option C: Internal Server**
- Upload to company server
- Send download link

## Communication Template

When sending updates to colleagues:

```
Subject: Webmix Sync Tool Update - v1.0.1

Hi team,

A new version of Webmix Sync Tool is available: v1.0.1

What's new:
✅ Fixed: Rsync errors when syncing
✅ Fixed: Site configuration editing
✅ Improved: Path handling for the app

Download: [Link to DMG]
or: Attached to this message

Installation:
1. Quit the current app if running
2. Download and open the new DMG
3. Drag to Applications (replace existing)
4. Launch and test

Priority: Medium (update when convenient)
Required: No (current version still works)

Questions? Let me know!

Best,
[Your name]
```

## Quick Update Script

Use `./release.sh` to automate the build and versioning process.

## Tracking Versions

Keep a `CHANGELOG.md` file in the project:

```markdown
# Changelog

All notable changes to Webmix Sync Tool.

## [Unreleased]

## [1.0.1] - 2026-05-13
### Fixed
- Fixed rsync SSH command quoting
- Fixed sync items loading

## [1.0.0] - 2026-05-11
### Added
- Initial release
- WordPress API integration
- Site management
- Pull/Push/Watch operations
- SSH terminal
```

## Rollback Strategy

If an update has issues:

1. **Keep previous versions available**
   - Don't delete old DMG files immediately
   - Keep at least the last 2-3 versions

2. **Test thoroughly before wide distribution**
   - Install on your machine first
   - Test with 1-2 colleagues before sending to everyone

3. **Have rollback DMG ready**
   - "If you have issues, here's v1.0.0: [link]"

## User Data Protection

**Good news:** User data is separate from the app!

- Site configurations: `~/Library/Application Support/` (persists across updates)
- App settings: Stored in user's home directory
- Installing new version: **Does NOT** delete user data

Users can safely update by:
1. Dragging new app to Applications
2. Replacing the old one
3. All their sites and settings remain intact

## Version Check Feature (Future)

Consider adding an auto-update check:
- Add version number to GUI (e.g., in window title or About dialog)
- Optional: Check a URL/API for latest version on startup
- Notify users if update available

## Best Practices

1. **Always test updates yourself first**
2. **Keep old versions for at least 1 month**
3. **Document all changes, even small ones**
4. **Increment version number for every release**
5. **Use semantic versioning consistently**
6. **Include clear installation instructions**
7. **Mention if update is critical or optional**

## Emergency Fixes

For critical bugs:

```bash
# Quick patch release
# 1. Fix the bug
# 2. Update to 1.0.2 (patch increment)
# 3. Rebuild
./build-app.sh && ./create-dmg.sh

# 4. Rename
mv dist/Webmix-Sync-Starter-Installer.dmg dist/Webmix-Sync-Starter-v1.0.2-hotfix.dmg

# 5. Distribute immediately with "URGENT" in subject
```

## Version History Location

Store released versions:
```
releases/
├── Webmix-Sync-Starter-v1.0.0.dmg
├── Webmix-Sync-Starter-v1.0.1.dmg
└── CHANGELOG.md
```

Keep the `releases/` folder in `.gitignore` but on your local machine or shared drive.
