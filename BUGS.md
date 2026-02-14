# Known Issues

## Open

- [ ] #B001 — GitHub Actions CI broken: still references `python manage.py test` instead of `flask test`
- [ ] #B002 — Stale `__pycache__` directories contain `.cpython-37.pyc` files alongside `.cpython-312.pyc`
- [ ] #B003 — Dev `docker-compose.yml` has hardcoded secrets (SECRET_KEY, DB password) — acceptable for local dev but should use `.env` for consistency

## Fixed

_(none yet)_
