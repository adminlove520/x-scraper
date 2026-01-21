# Changelog

All notable changes to this project will be documented in this file.

## [2.1.0] - 2026-01-21

### Added
- **Following Monitor**: Real-time tracking of new follows by monitored users.
- **Admin Command System**:
    - `/admin_all_stats`: View global subscription statistics.
    - `/admin_view_user`: Inspect specific users' subscription lists.
    - `/admin_delete_for_user`: Administratively remove specific subscriptions.
- **Bearer Token Rotation**: Support for comma-separated tokens in `TWITTER_BEARER_TOKEN` with automatic failover on 429 errors.
- **Data Persistence**: Added `data/following_snapshot.json` to track following states across restarts.

### Improved
- **Slash Commands**: Added `/followers_delete` for user self-service.
- **Bot Interactions**: Enhanced push cards with user bios and engagement metrics.
- **Permissions**: Isolated command visibility; users can only see/delete their own subscriptions.
- **Workflow Stability**: Added `git pull --rebase` to GitHub Actions to prevent merge conflicts when pushing processed IDs.

## [2.0.0] - 2026-01-21

### Changed
- **Architecture**: Complete refactor into a modular `app/` structure.
- **Collection Engine**: Migrated from Selenium-based scraping to official X.com API v2 (Bearer Token).
- **Service Mode**: Transformed from a standalone script to a concurrent service (Bot + Engine).
- **Localization**: Full Chinese localization for `README.md` and guides.

## [1.0.0] - Prior versions
- Base version utilizing Selenium for Twitter data collection.
