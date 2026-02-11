# CLAUDE.md — Soundmaze InteractiveAudioGame

## What This Project Is

Soundmaze is an interactive audiobook platform where users listen to narrated stories and make choices about how the story continues. The core data structure is a **directed graph**: books contain waypoints (nodes) connected by options (edges). One waypoint per book is marked `start=True` as the entry point.

This is a **Flask backend** built on the hack4impact flask-base boilerplate (2019). We are modernizing it incrementally — do not rewrite from scratch.

## Project Phase

**Phase 1 (current):** Flask proof-of-concept. Get a working web app where users can browse books, listen to audio narration, make choices at decision points, and have their progress tracked. Mobile-browser-first UI.

**Phase 2 (future):** Native mobile app. Not in scope for any current work.

## Tech Stack

- Python 3.7 (migrating to 3.12), Flask, SQLAlchemy, Jinja2 templates
- PostgreSQL (Docker) or SQLite (local dev fallback)
- Redis + RQ for background jobs
- Docker Compose for local dev (Flask + Postgres + Redis + Adminer + Maildev + Worker)
- Semantic UI for frontend CSS (will be replaced)
- Flask-Migrate / Alembic for DB migrations

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

**With Docker (preferred):**
```bash
cd docker
docker-compose up --build
```
App at http://localhost:5000, Adminer at http://localhost:8080, Maildev at http://localhost:8081.

**Without Docker:**
```bash
export FLASK_APP=manage.py
export FLASK_CONFIG=development
flask run --host=0.0.0.0 --port=5000
```

**CLI commands:**
```bash
flask setup-dev          # Insert roles + admin user
flask test               # Run unit tests
flask recreate-db        # Drop and recreate all tables (dev only!)
flask add-fake-data -n 20  # Generate fake users
flask load-json-book <file.json>  # Import a book from JSON
flask run-worker         # Start RQ background worker
```

## Known Technical Debt (being addressed)

Active modernization is tracked in the project instructions file. Key issues:
- Dependencies pinned to 2019 versions — upgrading incrementally
- `itsdangerous.TimedJSONWebSignatureSerializer` removed in itsdangerous 2.1+
- `werkzeug.contrib.fixers` removed in Werkzeug 1.0+
- `raygun4py` hard dependency in config.py
- `SQLALCHEMY_COMMIT_ON_TEARDOWN` deprecated
- `Flask-RQ` abandoned, `Flask-SSLify` deprecated
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
