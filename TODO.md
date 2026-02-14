# TODO — Feature Ideas and Improvement Backlog

Items are roughly prioritized within each section. Move items to CHANGELOG.md when completed.

## Housekeeping (next cleanup session)

- [ ] Remove `app/static/ckeditor/` directory (unused, large)
- [ ] Remove boilerplate files: `app.json`, `circle.yml`, `Procfile`, `.codeclimate.yml`, `CONDUCT.md`
- [ ] Remove `README_flask_boilerplate.md`
- [ ] Clean stale `.cpython-37.pyc` from all `__pycache__` dirs
- [ ] Set up local virtual environment (deps are modern enough now)
- [ ] Docker cleanup: update `maildev/maildev` image, remove deprecated compose `version` key if present
- [ ] Audit codebase for scattered `# TODO` and `# FIXME` comments, consolidate here
- [ ] Tag current state as `v0.1.0`

## Infrastructure

- [ ] Fix GitHub Actions CI (`.github/workflows/run_tests.yml`)
- [ ] Ensure DB migrations work end-to-end (dev and prod)
- [ ] Add health check endpoint for production monitoring

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

- [ ] Replace Semantic UI with modern mobile-first CSS
- [ ] Extend audio player page (currently basic dark-themed version)
- [ ] Design and implement choice/decision moment UI
- [ ] Implement path tracking UI ("Your Path" bottom sheet)
- [ ] Implement library/explore page with filtering
- [ ] Bottom navigation bar

## Voice Input (stretch)

- [ ] Browser Speech Recognition API for choice selection
- [ ] "Say 1 for [option A], say 2 for [option B]" pattern
