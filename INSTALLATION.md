# Installation Instructions for Webmix Sync Tool

## Requirements

- macOS 10.13 or later
- Homebrew (for dependencies)

## Step 1: Install Dependencies

Open Terminal and run:

```bash
brew install fswatch rsync
```

## Step 2: Install the Application

1. Download `Webmix-Sync-Starter-vX.X.X.dmg`
2. Double-click the DMG file to open it
3. Drag "Webmix Sync Starter" to your Applications folder
4. Eject the DMG

## Step 3: Bypass macOS Security (First Launch Only)

⚠️ **Important:** Because this app is not signed with an Apple Developer certificate, you need to tell macOS to allow it.

### Option A: Terminal Command (Recommended)

Open Terminal and paste this command:

```bash
sudo xattr -rd com.apple.quarantine "/Applications/Webmix Sync Tool.app"
```

Enter your Mac password when prompted.

### Option B: Right-Click Method

1. In Finder, navigate to Applications
2. Find "Webmix Sync Tool"
3. **Right-click** (or Control+click) the app
4. Select "Open" from the menu
5. In the security dialog, click "Open"

You only need to do this once. After that, you can open the app normally.

## Step 4: First Launch Setup

When you first open the app:

1. Go to **Settings → Preferences**
2. Enter your WordPress credentials:
   - WordPress URL (e.g., https://example.com)
   - Your WordPress username
   - Application Password (see below)

### Creating a WordPress Application Password

1. Log into your WordPress admin panel
2. Go to **Users → Your Profile**
3. Scroll down to "Application Passwords"
4. Enter a name (e.g., "Sync Tool")
5. Click "Add New Application Password"
6. Copy the generated password
7. Paste it into the app's settings

## Step 5: Configure SSH Access

In Settings → SSH & Sync:

1. Set your SSH key path (default: `~/.ssh/id_rsa`)
2. Set your default local root folder (e.g., `~/Sites`)
3. Click "Save"

## Step 6: Add Sites

1. Click "Sync API" to load sites from WordPress
2. Click "New Site" to configure a site
3. Enter SSH credentials and sync paths
4. Click "Save"

## Your Data Location

All your settings and site configurations are stored in:
```
~/Library/Application Support/Webmix Sync Tool/
```

This means your settings **persist across app updates** - you won't need to reconfigure when installing a new version.

## Updating to a New Version

1. Download the new DMG
2. Drag the new app to Applications (replace the old one)
3. Your settings and site configurations are automatically preserved
4. No need to bypass security again (macOS remembers your choice)

## Troubleshooting

### "App cannot be opened" error

If you see a security warning, follow Step 3 above to bypass Gatekeeper.

### Dependencies not found

Make sure fswatch and rsync are installed:
```bash
which fswatch  # Should show: /opt/homebrew/bin/fswatch
which rsync    # Should show: /usr/bin/rsync
```

If missing, install via Homebrew:
```bash
brew install fswatch rsync
```

### Settings not saved

Your settings are stored in Application Support. Check that the directory exists:
```bash
ls -la ~/Library/Application\ Support/Webmix\ Sync\ Tool/
```

You should see:
- `app-settings.json` (your credentials)
- `sites/` directory (your site configurations)

### SSH connection issues

Test SSH manually in Terminal:
```bash
ssh -i ~/.ssh/id_rsa username@hostname
```

Make sure:
- Your SSH key exists and has correct permissions (600)
- The server allows SSH key authentication
- You've added your public key to the server's `~/.ssh/authorized_keys`

## Support

For issues or questions, contact the development team.
