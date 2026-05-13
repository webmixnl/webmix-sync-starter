# Changelog

All notable changes to Webmix Sync Tool will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- TBD

## [1.0.5] - 2026-05-13

### Changed
- **Renamed application from "Webmix Sync Tool" to "Webmix Sync Starter"**
- Application Support directory renamed to `~/Library/Application Support/Webmix Sync Starter/`
- Automatic migration from old directory name on first launch
- Scripts now check both old and new directory names for backwards compatibility during transition

## [1.0.4] - 2026-05-13

### Fixed
- Shell scripts (pull, push, watch) now correctly look for site configurations in Application Support directory
- Fixed "Site config not found" error when running sync operations from bundled app
- Scripts now check Application Support first, then fall back to project directory for development mode
- Edit site dialog now correctly loads existing sync items from Application Support directory
- Fixed issue where editing a site would show default sync items instead of the configured ones

## [1.0.3] - 2026-05-13

### Fixed
- Settings and site configurations now persist across app updates
- User data (credentials, site configs) now stored in `~/Library/Application Support/Webmix Sync Tool/`
- Automatic migration of existing settings and sites from app bundle to Application Support on first launch

### Added
- Ad-hoc code signing in build process to reduce (but not eliminate) security warnings
- INSTALLATION.md with detailed user installation instructions including Gatekeeper bypass
- CODESIGNING.md with code signing information for developers
- Build script now includes signing step and security warning notes

### Documentation
- Updated README.md with security warning information and installation guide links
- Added clear instructions for end users on how to bypass macOS Gatekeeper warnings

## [1.0.2] - 2026-05-13

### Changed
- Redesigned UI with modern, minimalistic aesthetic using neutral gray color scheme
- Improved terminal/console readability with light background and high-contrast text colors
- Better visual distinction between button states (enabled, disabled, active)
- Watch button now displays subtle green when active, subtle red when inactive
- Reorganized action buttons into logical groups (Site Actions vs General)
- Converted icon-only buttons to text labels for better clarity (Refresh, New Site, Sync API, Edit)

### Removed
- Hidden SSH terminal button (temporarily disabled, kept in code for future implementation)
- Hidden Maintenance button (temporarily disabled, kept in code for future implementation)  
- Hidden Dev Setup button (temporarily disabled, kept in code for future implementation)

## [1.0.1] - 2026-05-13

### Changed
- Minor bug fixes and improvements

## [1.0.0] - 2026-05-13

### Added
- Initial release of Webmix Sync Tool
- WordPress REST API integration for site management
- Automatic site discovery from WordPress API
- Manual site configuration support
- Pull operation (remote → local sync)
- Push operation (local → remote sync)
- Watch mode (auto-sync on file changes)
- Embedded SSH terminal for direct server access
- Settings management with WordPress credentials
- SSH connection testing
- Real-time command output display
- Multi-site support with dropdown selector
- Site configuration editor
- Persistent settings storage

### Technical
- Built with PyQt5 for native macOS interface
- Bundled as standalone .app using py2app
- Includes Python 3.14 runtime
- DMG installer for easy distribution
- Supports macOS 10.13+

### Requirements
- macOS 10.13 or later
- `fswatch` and `rsync` (via Homebrew)
- SSH key authentication
- WordPress credentials (username + application password)
