#!/bin/bash
set -e

# Wait for Postgres to be ready
until python -c "
import os, sqlalchemy
url = os.environ.get('DEV_DATABASE_URL') or os.environ.get('DATABASE_URL', '')
if url:
    engine = sqlalchemy.create_engine(url)
    engine.connect().close()
    print('Postgres is ready')
" 2>/dev/null; do
    echo "Waiting for Postgres..."
    sleep 1
done

# Check if database is already initialized (books table has rows)
NEEDS_SETUP=$(python -c "
import os, sqlalchemy
url = os.environ.get('DEV_DATABASE_URL') or os.environ.get('DATABASE_URL', '')
engine = sqlalchemy.create_engine(url)
try:
    with engine.connect() as conn:
        result = conn.execute(sqlalchemy.text('SELECT COUNT(*) FROM books'))
        count = result.scalar()
        print('no' if count > 0 else 'yes')
except Exception:
    print('yes')
" 2>/dev/null || echo "yes")

if [ "$NEEDS_SETUP" = "yes" ]; then
    echo "First run detected — running setup-demo..."
    flask setup-demo
    echo "Setup complete."
else
    echo "Database already initialized, skipping setup."
fi

# Hand off to the CMD (flask run, gunicorn, etc.)
exec "$@"
