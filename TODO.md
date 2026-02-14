# TODO — Feature Ideas and Improvement Backlog

Items are roughly prioritized within each section. Move items to CHANGELOG.md when completed.

## Housekeeping (next cleanup session)

- [ ] Remove `app/static/ckeditor/` directory (unused, large)
- [ ] Remove boilerplate files: `app.json`, `circle.yml`, `Procfile`, `.codeclimate.yml`, `CONDUCT.md`
- [ ] Remove `README_flask_boilerplate.md`
- [ ] Remove empty `app/main/forms.py` (unused boilerplate placeholder)
- [ ] Clean stale `.cpython-37.pyc` from all `__pycache__` dirs
- [ ] Set up local virtual environment (deps are modern enough now)
- [ ] Docker cleanup: update `maildev/maildev` image, remove deprecated compose `version` key if present
- [x] Audit codebase for scattered `# TODO` and `# FIXME` comments — none found
- [x] Tag current state as `v0.1.0`

## Auth & Email (PRIORITY)

- [ ] Set up production mail server (configure SMTP credentials in `.env`)
- [ ] Enable email confirmation flow for new user registration
- [ ] Enable password reset via email
- [ ] Test full registration → confirmation → login flow on production

## Admin

- [ ] Enable Adminer (or equivalent) on production for direct DB access
- [ ] Review admin panel functionality — ensure user management works end-to-end

## Infrastructure

- [ ] Fix GitHub Actions CI (`.github/workflows/run_tests.yml`)
- [ ] Ensure DB migrations work end-to-end (dev and prod)
- [ ] Add health check endpoint for production monitoring
- [ ] Test book upload (JSON + audio) on production server

## Data Model Extensions

- [ ] Add book metadata: genre, cover_url, narrator, language, duration, publisher
- [ ] Add UserSession model: user_id, book_id, current_waypoint_id, path_history
- [ ] Add category/genre model
- [ ] Add review/rating model
- [ ] Extend JSON book format to support new metadata fields

## REST API

- [ ] Create `app/api/` blueprint
- [ ] Expose books, waypoints, options as JSON endpoints
- [ ] Auth via token (JWT or Flask-Login session)

## Audio

- [ ] Integrate TTS service (browser Web Speech API for PoC, or server-side)
- [ ] Audio file upload/management for pre-recorded content
- [ ] Add audio content type to waypoints

## UI / UX

- [ ] Add exit/back button to audio player
- [ ] Replace Semantic UI with modern mobile-first CSS
- [ ] Extend audio player page (currently basic dark-themed version)
- [ ] Design and implement choice/decision moment UI
- [ ] Implement path tracking UI ("Your Path" bottom sheet)
- [ ] Implement session logging — track user progress through a book (current waypoint, path taken)
- [ ] Implement library/explore page with filtering
- [ ] Bottom navigation bar

## Voice Input (stretch)

- [ ] Browser Speech Recognition API for choice selection
- [ ] "Say 1 for [option A], say 2 for [option B]" pattern
