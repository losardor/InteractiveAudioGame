# CLAUDE.md — Soundmaze InteractiveAudioGame

## What This Project Is

Soundmaze is an interactive audiobook platform where users listen to narrated stories and make choices about how the story continues. The core data structure is a **directed graph**: books contain waypoints (nodes) connected by options (edges). One waypoint per book is marked `start=True` as the entry point.

This is a **Flask backend** built on the hack4impact flask-base boilerplate (2019). We are modernizing it incrementally — do not rewrite from scratch.

## Project Phase

**Phase 1 (current):** Flask proof-of-concept. Get a working web app where users can browse books, listen to audio narration, make choices at decision points, and have their progress tracked. Mobile-browser-first UI.

**Phase 2 (future):** Native mobile app. Not in scope for any current work.

## Tech Stack

- Python 3.12, Flask 3.1, SQLAlchemy 2.0, Jinja2 3.1
- PostgreSQL (Docker) or SQLite (local dev fallback)
- Redis 5.2 + RQ 2.1 for background jobs (direct usage, no Flask-RQ wrapper)
- Docker Compose for local dev (Flask + Postgres + Redis + Adminer + Maildev + Worker)
- Semantic UI for frontend CSS (will be replaced)
- Flask-Migrate 4.1 / Alembic for DB migrations
- WTForms 3.2 + wtforms-sqlalchemy for forms

## Domain Model

```
Book (id, name, description, owner_id)
  └── Waypoint (id, book_id, start:bool)
        ├── TextContent (id, waypoint_id, content:text)
        └── Option (id, sourceWaypoint_id, destinationWaypoint_id, linkText)
User (id, email, password_hash, role_id, books[])
Role (id, name, permissions)
```

## Directory Structure / Module Map

```
app/
├── __init__.py          # App factory (create_app), extension init
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
├── static/              # Compiled output + vendor libs (ckeditor, fonts)
├── assets.py            # Flask-Assets bundle definitions
├── decorators.py
├── email.py             # send_email helper
└── utils.py             # Jinja template utilities
config.py                # Config classes (Dev/Test/Prod/Heroku/Unix)
manage.py                # CLI entry point (FLASK_APP=manage.py)
docker/
├── Dockerfile
└── docker-compose.yml
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
        "content": {"type": "text", "data": "Story text here"},
        "options": [{
            "destinationWaypoint_id": 2,
            "linkText": "Go to chapter 2"
        }]
    }]
}
```

Content type `"text"` is the only implemented type. Future types: `"audio"`, `"tts"`.

## Running Locally

**With Docker (preferred and canonical):**
```bash
cd docker
docker-compose up --build
```
App at http://localhost:5000, Adminer at http://localhost:8080, Maildev at http://localhost:8081.

**Without Docker (requires local venv — NOT currently set up):**
```bash
export FLASK_APP=manage.py
export FLASK_CONFIG=development
flask run --host=0.0.0.0 --port=5000
```
Note: Running locally without Docker requires a virtual environment with all dependencies installed. The pinned 2019 dependency versions in `requirements.txt` may not compile on Python 3.10+. Until dependencies are modernized (Step 1 of the roadmap), **use Docker for all testing and running.**

**CLI commands:**
```bash
flask setup-dev          # Insert roles + admin user
flask test               # Run unit tests
flask recreate-db        # Drop and recreate all tables (dev only!)
flask add-fake-data -n 20  # Generate fake users
flask load-json-book <file.json>  # Import a book from JSON
flask run-worker         # Start RQ background worker
```

## Testing

### Test Environment

**Docker is the canonical test environment.** Dependencies are now modern (Flask 3.1, Python 3.12) and should install on the host machine's Python 3.10+, but no local virtual environment has been set up yet. Docker remains the primary way to run and test.

### Running Tests

```bash
# Build and run tests inside Docker (one-shot, no leftover container)
cd docker
docker-compose build flask
docker-compose run --rm flask flask test
```

For interactive debugging inside the container:
```bash
docker-compose run --rm flask bash
# then inside the container:
export FLASK_APP=manage.py
export FLASK_CONFIG=testing
flask test
```

### Existing Test Suite

Tests live in `tests/` and are auto-discovered by `unittest.TestLoader().discover('tests')`.

| File | Tests | What it covers |
|------|-------|----------------|
| `test_basics.py` | 2 | App factory boots, testing config is active |
| `test_user_model.py` | 16 | Password hashing, confirmation/reset/email-change tokens, roles & permissions, anonymous user |

Total: **18 tests**. All use SQLite in-memory via the `testing` config. No external services (Postgres, Redis) needed.

### Verification Protocol for Modernization Commits

After each infrastructure commit, run this sequence:

1. **Syntax check** (fast, no Docker): `python3 -c "import ast; ast.parse(open('manage.py').read())"`
2. **Full test suite** (Docker): `docker-compose run --rm flask flask test`
3. **App boot check** (Docker): `docker-compose run --rm flask flask --help` — should list all registered CLI commands
4. **Smoke test** (Docker): `docker-compose up` then visit http://localhost:5000

All 18 tests must pass. Any failure means the commit broke something — fix before moving on.

### CI / GitHub Actions

File: `.github/workflows/run_tests.yml`

Currently **broken** — still references `python manage.py test` (pre-Flask-CLI). Needs updating to `flask test` with `FLASK_APP=manage.py` set. Tracked as a task in the modernization roadmap.

## Known Technical Debt (being addressed)

Active modernization is tracked in the project instructions file (`SOUNDMAZE_PROJECT.md`). 

**Resolved (Commits 1–3 on modernize/flask-cli branch):**
- ~~Dependencies pinned to 2019 versions~~ → All updated to current stable
- ~~`flask_script`~~ → Flask CLI
- ~~`itsdangerous.TimedJSONWebSignatureSerializer`~~ → `URLSafeTimedSerializer`
- ~~`werkzeug.contrib.fixers`~~ → `werkzeug.middleware.proxy_fix`
- ~~`raygun4py` hard dependency~~ → Removed
- ~~`SQLALCHEMY_COMMIT_ON_TEARDOWN`~~ → Removed
- ~~`Flask-RQ` abandoned~~ → Replaced with `get_queue()` helper using `rq` directly
- ~~`Flask-SSLify` deprecated~~ → Removed
- ~~Python 3.7 in Docker~~ → Python 3.12

**Remaining:**
- GitHub Actions CI still broken (references old `python manage.py test`)
- No local virtual environment set up
- Docker compose `version: "3.7"` key deprecated, maildev image outdated
- No API layer — everything is server-rendered Jinja templates
- No audio content, session tracking, or mobile-optimized UI yet

## Files to Ignore

- `app/static/ckeditor/` — bundled CKEditor, not actively used
- `app/static/fonts/` — Semantic UI icon fonts (will be replaced)
- `README_flask_boilerplate.md` — original boilerplate docs
- `app.json`, `circle.yml`, `Procfile` — Heroku deployment (not used)

## Scoping Rules

- Each task should focus on ONE module from the directory map above
- Don't refactor files outside the task scope
- Commit frequently with clear messages
- When adding new modules, update this file
