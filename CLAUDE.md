# CLAUDE.md — Soundmaze InteractiveAudioGame

## What This Project Is

Soundmaze is an interactive audiobook platform where users listen to narrated stories and make choices about how the story continues. The core data structure is a **directed graph**: books contain waypoints (nodes) connected by options (edges). One waypoint per book is marked `start=True` as the entry point.

This is a **Flask backend** built on the hack4impact flask-base boilerplate (2019), now modernized to current dependencies. The app is live in production.

## Project Phase

**Phase 1 (current):** Flask proof-of-concept. A working web app where users can browse books, listen to audio narration, make choices at decision points, and have their progress tracked. Mobile-browser-first UI.

**Phase 2 (future):** Native mobile app. Not in scope for any current work.

## Tech Stack

- Python 3.12, Flask 3.1, SQLAlchemy 2.0, Jinja2 3.1
- PostgreSQL (Docker dev + production VPS)
- Redis 5.2 + RQ 2.1 for background jobs (direct usage, no Flask-RQ wrapper)
- Docker Compose for local dev (Flask + Postgres + Redis + Adminer + Maildev + Worker)
- Docker Compose (prod variant) + Caddy reverse proxy for production
- Semantic UI for frontend CSS (will be replaced)
- Flask-Migrate 4.1 / Alembic for DB migrations
- WTForms 3.2 + wtforms-sqlalchemy for forms
- Gunicorn for production WSGI server

## Domain Model

```
Book (id, name, description, owner_id)
  └── Waypoint (id, book_id, start:bool)
        ├── TextContent (id, waypoint_id, content:text)
        └── Option (id, sourceWaypoint_id, destinationWaypoint_id, linkText)
User (id, email, password_hash, role_id, books[])
Role (id, name, permissions)
```

## Directory Structure

```
app/
├── __init__.py          # App factory (create_app), extension init, get_queue() helper
├── account/             # Auth: registration, login, sessions, roles
├── admin/               # Admin panel, user management
├── books/               # Book/Waypoint/Option CRUD, JSON loader
│   ├── view.py
│   ├── forms.py
│   └── loader.py        # JsonFileBookLoader — parses JSON into Book graph
├── main/                # Landing page, error handlers
├── models/
│   ├── book.py
│   ├── waypoint.py
│   ├── option.py
│   ├── content.py       # TextContent model
│   ├── user.py          # User, Role, Permission, login_manager setup
│   └── miscellaneous.py # EditableHTML (boilerplate, largely unused)
├── templates/           # Jinja2, organized by blueprint
├── assets/              # Source SCSS/JS (processed by Flask-Assets)
├── static/              # Compiled output + vendor libs
│   └── audio/           # Audio files organized by book (e.g., audio/demo/*.mp3)
├── assets.py            # Flask-Assets bundle definitions
├── decorators.py
├── email.py             # send_email helper
└── utils.py             # Jinja template utilities

config.py                # Config classes (Dev/Test/Prod/Unix)
manage.py                # CLI entry point (FLASK_APP=manage)
requirements.txt         # Pinned dependencies (all current stable versions)

docker/
├── Dockerfile           # Python 3.12 based
└── docker-compose.yml   # Dev environment

docker-compose.prod.yml  # Production (Caddy + Gunicorn + Postgres + Redis)
Caddyfile                # Reverse proxy config (app.soundmaze.it)
.env.template            # Production env var template
setup-vps.sh             # VPS initial setup script
DEPLOYMENT.md            # Full production deployment guide
```

## Code Conventions

- New models go in `app/models/` as separate files, imported via `app/models/__init__.py`
- New feature areas get their own **Blueprint** in `app/<feature>/`
- Templates follow `templates/<blueprint>/` structure
- Database changes always via Flask-Migrate migrations, never `recreate_db` in non-dev
- Python style: follow existing patterns in the codebase

## JSON Book Format

```json
{
    "name": "Book Title",
    "description": "Book description",
    "waypoints": [{
        "id": 1,
        "start": true,
        "content": {"type": "text", "data": "Story text here", "audio": "chapter1.mp3"},
        "options": [{
            "destinationWaypoint_id": 2,
            "linkText": "Go to chapter 2"
        }]
    }]
}
```

Content type `"text"` is the only implemented type. Future types: `"tts"`.

The `"audio"` field in content is **optional**. When present, the loader sets `audio_url` to `/static/audio/<book_id>/<filename>`. The actual audio file must be placed at that path manually or via upload.

---

## Git Workflow

### Branch Naming

- `fix/short-description` — bug fixes
- `feature/short-description` — new features
- `chore/short-description` — cleanup, maintenance, docs

### Rules

- **`main` always reflects what's running in production.** Everything else branches off it.
- Commit directly to `main` only for trivial zero-risk changes (typo, comment, tested config tweak).
- Everything else gets a branch. Branches should live hours to a couple of days, not weeks.
- Never mix bug fixes with feature work in the same branch.
- Multiple small unrelated fixes can be batched into one `fix/batch-minor-fixes` branch.

### Merge and Deploy Cycle

1. Create branch from `main`
2. Work on it (commit often with clear messages)
3. Test in Docker locally — full flow, not just the changed thing
4. Merge to `main`
5. Push to GitHub
6. On VPS: `git pull` → `docker compose -f docker-compose.prod.yml up -d --build`
7. Quick smoke test on production

### Commit Messages

Use clear, descriptive messages. Examples:
- `fix: correct text contrast on waypoint options`
- `feature: add session tracking model and migration`
- `chore: remove unused ckeditor assets`

---

## Issue Tracking

Three files in the repo root track work:

- **`BUGS.md`** — Known issues. Each gets an ID (e.g., `#B001`). Mark as fixed with commit hash when done.
- **`TODO.md`** — Feature ideas and improvements backlog, roughly prioritized.
- **`CHANGELOG.md`** — What changed in each deployment/version.

When you encounter a bug or improvement while working on something else, add it to the appropriate file and stay in scope. Don't fix unrelated things in the same branch.

---

## Running Locally

**With Docker (canonical):**
```bash
cd docker
docker-compose up --build
```
App at http://localhost:5000, Adminer at http://localhost:8080, Maildev at http://localhost:8081.

**CLI commands (inside Docker container or with FLASK_APP=manage set):**
```bash
flask setup-dev          # Insert roles + admin user
flask test               # Run unit tests
flask recreate-db        # Drop and recreate all tables (dev only!)
flask add-fake-data -n 20  # Generate fake users
flask load-json-book <file.json>  # Import a book from JSON
flask run-worker         # Start RQ background worker
```

---

## Production Deployment

**Live at:** https://app.soundmaze.it

**Infrastructure:** Aruba Cloud VPS (Ubuntu 24.04), Docker Compose, Caddy (automatic HTTPS), PostgreSQL 16, Redis 7, Gunicorn.

**Deploying updates:**
```bash
ssh deploy@<VPS_IP>
cd ~/soundmaze
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

**Database migrations on production:**
```bash
docker compose -f docker-compose.prod.yml exec flask flask db upgrade
```

**Full deployment guide:** See `DEPLOYMENT.md` in this repo for initial setup, DNS, backups, and troubleshooting.

**Key production files in this repo:**
- `docker-compose.prod.yml` — Production services (Caddy, Gunicorn, Postgres, Redis, Worker)
- `Caddyfile` — Reverse proxy routing
- `.env.template` — Required environment variables (copy to `.env` on server)
- `setup-vps.sh` — Initial VPS hardening and Docker install

---

## Testing

### Running Tests

```bash
# One-shot (build + run + cleanup)
cd docker
docker-compose build flask
docker-compose run --rm flask flask test

# Interactive
docker-compose run --rm flask bash
export FLASK_APP=manage
export FLASK_CONFIG=testing
flask test
```

### Test Suite

Tests in `tests/`, auto-discovered by `unittest`. All use SQLite in-memory — no Postgres or Redis needed.

| File | Tests | Coverage |
|------|-------|----------|
| `test_basics.py` | 2 | App factory boots, testing config loads |
| `test_user_model.py` | 16 | Password hashing, tokens, roles, permissions, anonymous user |

**Total: 18 tests.**

### Verification After Infrastructure Changes

1. **Syntax check** (no Docker): `python3 -c "import ast; ast.parse(open('manage.py').read())"`
2. **Test suite**: `docker-compose run --rm flask flask test` — all 18 must pass
3. **CLI check**: `docker-compose run --rm flask flask --help` — commands listed
4. **Full boot**: `docker-compose up` → http://localhost:5000 loads

---

## Remaining Technical Debt

- GitHub Actions CI broken (`.github/workflows/run_tests.yml` still references `python manage.py test`)
- No local virtual environment set up (Docker works fine, but venv would speed up quick checks)
- Dev `docker-compose.yml` has hardcoded secrets (acceptable for local dev, but noted)
- `app/static/ckeditor/` — bundled CKEditor, unused, should be removed
- `app/static/fonts/` — Semantic UI icon fonts (will go when Semantic UI is replaced)
- Boilerplate files from original scaffold: `app.json`, `circle.yml`, `Procfile`, `.codeclimate.yml`
- `__pycache__` directories with stale `.cpython-37.pyc` files (harmless but messy)
- No API layer — everything is server-rendered Jinja templates
- No session/progress tracking model
- No mobile-optimized UI

---

## Module Map (for scoping sessions)

Each session should focus on ONE module. Don't refactor outside scope.

```
MODULE: auth
  Files: app/account/*, app/models/user.py, app/models/miscellaneous.py
  Templates: templates/account/*

MODULE: books-core
  Files: app/models/book.py, app/models/waypoint.py, app/models/option.py, app/models/content.py
  Files: app/books/view.py, app/books/forms.py, app/books/loader.py
  Templates: templates/books/*

MODULE: admin
  Files: app/admin/*
  Templates: templates/admin/*

MODULE: infra
  Files: config.py, manage.py, requirements.txt, docker/*, docker-compose.prod.yml, Caddyfile, app/__init__.py

MODULE: frontend
  Files: app/templates/*, app/assets/*, app/static/*, app/assets.py

MODULE: audio (TO BE CREATED)
  Purpose: TTS generation, audio file management, playback API

MODULE: session-tracking (TO BE CREATED)
  Purpose: Track user progress through a book (current waypoint, path history)

MODULE: api (TO BE CREATED)
  Purpose: REST API layer for frontend/mobile consumption
```

---

## Files to Ignore

- `app/static/ckeditor/` — bundled CKEditor, not actively used
- `app/static/fonts/` — Semantic UI icon fonts (will be replaced)
- `README_flask_boilerplate.md` — original boilerplate docs
- `app.json`, `circle.yml`, `Procfile` — Heroku deployment (not used)
- `.codeclimate.yml` — Code Climate config (not used)
- `CONDUCT.md` — boilerplate code of conduct

---

## Scoping Rules

- Each task focuses on ONE module from the map above
- Don't refactor files outside the task scope
- If you notice an unrelated issue, add it to `BUGS.md` or `TODO.md` and move on
- Commit frequently with clear messages
- When adding new modules, update this file
