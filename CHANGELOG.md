# Changelog

All notable changes to Soundmaze are documented here. Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

- Established development workflow (three-loop system, git branching conventions)
- Created BUGS.md, TODO.md, CHANGELOG.md for issue tracking
- Updated CLAUDE.md and SOUNDMAZE_PROJECT.md to reflect current state

## [0.1.0] — 2025-02-14 (baseline)

Everything up to this point, retroactively documented.

### Infrastructure Modernization
- Upgraded from Python 3.7 → 3.12, Flask 1.1 → 3.1, SQLAlchemy 1.x → 2.0
- Replaced deprecated flask_script with Flask CLI
- Replaced deprecated itsdangerous.TimedJSONWebSignatureSerializer with URLSafeTimedSerializer
- Replaced werkzeug.contrib.fixers with werkzeug.middleware.proxy_fix
- Removed abandoned Flask-RQ, replaced with direct rq usage via get_queue() helper
- Removed raygun4py hard dependency
- Fixed WTForms 3.x, rq 2.x, SQLAlchemy 2.0, Flask 3.x breaking changes
- All 18 tests passing on modern stack

### Production Deployment
- Deployed to Aruba Cloud VPS (Ubuntu 24.04)
- Docker Compose production setup with Caddy, Gunicorn, PostgreSQL 16, Redis 7
- Automatic HTTPS via Let's Encrypt
- Live at app.soundmaze.it

### Features
- User auth (register, login, roles, admin panel)
- Book CRUD with JSON upload and directed-graph navigation
- Audio player with dark-themed immersive UI
- JSON book loader with optional audio field support
- Markdown-to-JSON story converter (md2soundmaze.py)
- Landing page at soundmaze.it integrated with app

### Content Authoring
- Markdown story format with standard syntax (headings, links, blockquotes)
- Converter with validation for broken links, missing waypoints, unreachable content
