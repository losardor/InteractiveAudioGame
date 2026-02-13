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

# Check if the database tables exist at all
TABLES_EXIST=$(python -c "
import os, sqlalchemy
url = os.environ.get('DEV_DATABASE_URL') or os.environ.get('DATABASE_URL', '')
engine = sqlalchemy.create_engine(url)
try:
    with engine.connect() as conn:
        conn.execute(sqlalchemy.text('SELECT 1 FROM roles LIMIT 1'))
        print('yes')
except Exception:
    print('no')
" 2>/dev/null || echo "no")

if [ "$TABLES_EXIST" = "no" ]; then
    echo "First run detected — running setup-demo (creates DB, roles, admin, demo book)..."
    flask setup-demo
    echo "Setup complete."
else
    # Tables exist — ensure roles and admin user are present (idempotent)
    echo "Database tables exist. Ensuring roles and admin user..."
    flask setup-prod

    # Load demo book only if books table is empty
    NEEDS_DEMO=$(python -c "
import os, sqlalchemy
url = os.environ.get('DEV_DATABASE_URL') or os.environ.get('DATABASE_URL', '')
engine = sqlalchemy.create_engine(url)
try:
    with engine.connect() as conn:
        result = conn.execute(sqlalchemy.text('SELECT COUNT(*) FROM books'))
        count = result.scalar()
        print('no' if count > 0 else 'yes')
except Exception:
    print('no')
" 2>/dev/null || echo "no")

    if [ "$NEEDS_DEMO" = "yes" ]; then
        echo "Books table is empty — loading demo book..."
        flask load-json-book enchanted_forest.json
    else
        echo "Books already loaded, skipping demo content."
    fi
fi

# Hand off to the CMD (flask run, gunicorn, etc.)
exec "$@"
