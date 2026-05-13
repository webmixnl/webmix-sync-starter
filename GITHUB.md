# GitHub Setup Guide

This guide helps you safely upload Webmix Sync Tool to GitHub for version control and collaboration.

## ✅ Pre-Upload Checklist

The `.gitignore` has been configured to exclude:
- ✅ Build artifacts (`build/`, `dist/`)
- ✅ Virtual environments (`venv/`, `env/`)
- ✅ **Site credentials** (`config/sites/*.env` - except example)
- ✅ **App settings** (`config/app-settings.json`)
- ✅ SSH keys (`*.pem`, `*.key`, `id_rsa*`)
- ✅ Logs (`logs/`)
- ✅ macOS files (`.DS_Store`)
- ✅ IDE files (`.vscode/`, `.idea/`)

## 🚀 Initial Setup

### 1. Initialize Git Repository

```bash
cd /Users/bram/wp-sync-starter
git init
git add .
git commit -m "Initial commit: Webmix Sync Tool v1.0.0"
```

### 2. Create GitHub Repository

**Option A: Via GitHub Website**
1. Go to https://github.com/new
2. Repository name: `webmix-sync-tool` (or your choice)
3. Choose: **Private** (recommended for internal tools)
4. Don't initialize with README (you already have one)
5. Click "Create repository"

**Option B: Via GitHub CLI**
```bash
# Install GitHub CLI if needed
brew install gh

# Authenticate
gh auth login

# Create private repo
gh repo create webmix-sync-tool --private --source=. --remote=origin
```

### 3. Connect and Push

```bash
# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/webmix-sync-tool.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## 🔒 Security Best Practices

### What's Safe to Commit ✅
- Source code (`gui/`, `bin/`, `lib/`)
- Build scripts (`build-app.sh`, `create-dmg.sh`, `release.sh`)
- Documentation (`*.md`)
- Example configs (`config/sites/example-site.env`)
- Excludes list (`config/excludes.txt`)
- Setup script (`setup.py`)

### What's NEVER Committed ❌
- Real site configs (`config/sites/alfabier.env`, etc.)
- App settings with credentials (`config/app-settings.json`)
- Built applications (`dist/*.app`, `*.dmg`)
- SSH keys (any `.pem`, `.key` files)
- Logs with potential sensitive data

## 📂 Repository Structure on GitHub

```
webmix-sync-tool/
├── .gitignore              ✅ Committed
├── README.md               ✅ Committed
├── BUILD.md                ✅ Committed
├── CHANGELOG.md            ✅ Committed
├── DISTRIBUTION.md         ✅ Committed
├── UPDATE-WORKFLOW.md      ✅ Committed
├── GITHUB.md               ✅ Committed (this file)
├── setup.py                ✅ Committed
├── build-app.sh            ✅ Committed
├── create-dmg.sh           ✅ Committed
├── release.sh              ✅ Committed
├── bin/                    ✅ Committed
│   ├── pull
│   ├── push
│   ├── watch
│   └── setup-site
├── config/
│   ├── excludes.txt        ✅ Committed
│   ├── sites/
│   │   ├── example-site.env    ✅ Committed (template)
│   │   ├── alfabier.env        ❌ Ignored
│   │   └── livebetalen.env     ❌ Ignored
│   └── app-settings.json   ❌ Ignored
├── gui/
│   ├── wp-sync-native.py   ✅ Committed
│   ├── requirements.txt    ✅ Committed
│   └── app-icon.icns       ✅ Committed
└── lib/
    └── common.sh           ✅ Committed
```

## 👥 Team Collaboration

### For Team Members to Use:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/webmix-sync-tool.git
   cd webmix-sync-tool
   ```

2. **Set up for development:**
   ```bash
   # Install dependencies
   cd gui
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Create their own site configs:**
   ```bash
   cp config/sites/example-site.env config/sites/mysite.env
   # Edit mysite.env with their credentials
   ```

4. **Build their own app (if needed):**
   ```bash
   ./build-app.sh
   ```

### For You to Push Updates:

```bash
# After making changes
git add .
git commit -m "Fixed rsync SSH command quoting"
git push
```

### For Team to Pull Updates:

```bash
git pull
# Then rebuild if needed
./build-app.sh && ./create-dmg.sh
```

## 🏷️ Tagging Releases

For each version release:

```bash
# After running ./release.sh and creating v1.0.1
git add .
git commit -m "Release v1.0.1"
git tag v1.0.1
git push origin main --tags
```

This creates a tagged release on GitHub that team members can reference.

## 🔍 Verify Before First Push

**IMPORTANT:** Before your first push, verify no secrets will be committed:

```bash
# Check what will be committed
git status

# Should NOT see:
# - config/sites/alfabier.env (or other real sites)
# - config/app-settings.json
# - Any .pem or .key files
# - dist/ or build/ folders

# If you see sensitive files:
git rm --cached <file>
# Then update .gitignore and commit
```

## 🌐 Public vs Private Repository

**Recommended: Private** 🔒
- Internal company tool
- May contain business logic
- Safer for credentials management
- Free private repos on GitHub

**Consider Public if:**
- You want to open-source the tool
- All company-specific logic is removed
- No proprietary integrations
- Want community contributions

## 📝 README for GitHub

Your existing [README.md](README.md) is already good for GitHub! It explains:
- What the tool does
- How to use it
- Requirements
- CLI and GUI usage

## 🔄 Workflow

### Daily Development:
```bash
# Make changes
# Test locally
git add .
git commit -m "Descriptive message"
git push
```

### Release New Version:
```bash
# Update code
./release.sh
# Enter version number
git add .
git commit -m "Release v1.0.1"
git tag v1.0.1
git push origin main --tags
```

## ⚠️ Common Mistakes to Avoid

1. ❌ **Don't commit credentials** - Always check `git status` before committing
2. ❌ **Don't commit built apps** - They're huge and change constantly
3. ❌ **Don't commit node_modules or venv** - Already in .gitignore
4. ❌ **Don't commit .DS_Store** - Already in .gitignore
5. ✅ **Do commit example configs** - They're templates for others
6. ✅ **Do keep .gitignore updated** - Add new sensitive patterns as needed

## 🛡️ Emergency: Accidentally Committed Secrets

If you accidentally commit credentials:

```bash
# Remove from git history (before pushing)
git rm --cached config/sites/mysite.env
git commit --amend -m "Remove accidentally committed config"

# If already pushed - you must:
# 1. Rotate all exposed credentials (SSH keys, passwords, etc.)
# 2. Force push (destructive): git push --force
# Or better: use git-filter-repo to clean history
```

## 💡 Tips

- **Branch strategy:** Use `main` for stable code, create feature branches for experiments
- **Commit messages:** Be descriptive: "Fixed SSH quoting bug" not "Fixed bug"
- **Pull before push:** Always `git pull` before `git push` when working with a team
- **Test before commit:** Make sure the app builds and works before committing

## 🎯 Quick Start Commands

```bash
# First time setup
git init
git add .
git commit -m "Initial commit: Webmix Sync Tool"
git remote add origin https://github.com/YOUR_USERNAME/webmix-sync-tool.git
git push -u origin main

# Verify no secrets committed
git log --stat | grep -E "\.env|app-settings\.json|\.pem|\.key"
# (should return nothing)
```

## 📞 Support

For GitHub-specific issues:
- GitHub Docs: https://docs.github.com
- GitHub CLI: https://cli.github.com

Your repository is now ready for version control and team collaboration! 🎉
