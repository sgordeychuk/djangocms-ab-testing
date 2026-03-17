# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-17

### Added
- A/B test container and variant CMS plugins
- Round-robin variant assignment with atomic database counter
- Cookie-based variant persistence (30 days)
- Event tracking API endpoint with CSRF protection
- Configurable tracking actions via `AB_TESTING_VALID_ACTIONS` setting
- Auto "view" event when variant is rendered
- Bootstrap modal event tracking (opened, closed, requested)
- Admin dashboard with Chart.js visualizations
- Per-variant stats (sessions, opens, requests, closes, conversion rate)
- Daily trends and conversion rate charts
- Distribution breakdowns by device, browser, OS, screen size
- Date range and device property filtering
- CSV export via django-import-export
- Cache control middleware for A/B tested pages
- `seed_ab_data` management command for test data generation
