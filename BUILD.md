# Building Webmix Sync Tool for Distribution

This guide explains how to build a distributable macOS application.

## Prerequisites

- macOS 10.13 or later
- Python 3.8+
- Homebrew (for fswatch and rsync dependencies)

## Quick Build

```bash
./build-app.sh
```

This will create `dist/Webmix Sync Tool.app` ready for distribution.

## Manual Build Steps

### 1. Create Virtual Environment

```bash
cd gui
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install py2app
```

### 3. Build the Application

From the project root:

```bash
python setup.py py2app
```

This creates:
- `build/` - temporary build files
- `dist/Webmix Sync Tool.app` - the standalone application

### 4. Test the Application

```bash
open "dist/Webmix Sync Tool.app"
```

## Distribution Options

### Option 1: Direct App Distribution

Simply share the `dist/Webmix Sync Tool.app` folder:
- Compress it: `cd dist && zip -r "Webmix Sync Tool.zip" "Webmix Sync Tool.app"`
- Share the ZIP file with colleagues
- They can unzip and drag to Applications folder

### Option 2: Create a DMG (Recommended)

```bash
./create-dmg.sh
```

This creates a professional installer DMG file that colleagues can:
1. Double-click to mount
2. Drag the app to Applications folder
3. Eject the DMG

## Requirements for End Users

End users need to install these command-line tools:

```bash
brew install fswatch rsync
```

The app will check for these on startup and prompt if missing.

## Notes

- The built app is **self-contained** and includes Python + all dependencies
- App size: ~170MB (includes Python runtime and PyQt5)
- First build takes 5-10 minutes
- Subsequent builds are faster
- Users need **SSH key authentication** set up for their servers
