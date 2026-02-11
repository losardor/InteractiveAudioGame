#!/usr/bin/env python
import os
import subprocess

import click
from flask_migrate import Migrate
from redis import Redis
from rq import Queue, Worker

from app import create_app, db
from app.models import Role, User
from config import Config

from app.books.loader import JsonFileBookLoader

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)


@app.cli.command()
def test():
    """Run the unit tests."""
    import unittest

    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@app.cli.command('recreate-db')
def recreate_db():
    """
    Recreates a local database. You probably should not use this on
    production.
    """
    db.drop_all()
    db.create_all()
    db.session.commit()


@app.cli.command('add-fake-data')
@click.option('-n', '--number-users', default=10, type=int,
              help='Number of each model type to create')
def add_fake_data(number_users):
    """
    Adds fake data to the database.
    """
    User.generate_fake(count=number_users)


@app.cli.command('setup-dev')
def setup_dev():
    """Runs the set-up needed for local development."""
    setup_general()


@app.cli.command('setup-prod')
def setup_prod():
    """Runs the set-up needed for production."""
    setup_general()


def setup_general():
    """Runs the set-up needed for both local development and production.
       Also sets up first admin user."""
    Role.insert_roles()
    admin_query = Role.query.filter_by(name='Administrator')
    if admin_query.first() is not None:
        if User.query.filter_by(email=Config.ADMIN_EMAIL).first() is None:
            user = User(
                first_name='Admin',
                last_name='Account',
                password=Config.ADMIN_PASSWORD,
                confirmed=True,
                email=Config.ADMIN_EMAIL)
            db.session.add(user)
            db.session.commit()
            print('Added administrator {}'.format(user.full_name()))


@app.cli.command('run-worker')
def run_worker():
    """Initializes a slim rq task queue."""
    listen = ['default']
    conn = Redis(
        host=app.config['RQ_DEFAULT_HOST'],
        port=app.config['RQ_DEFAULT_PORT'],
        db=0,
        password=app.config['RQ_DEFAULT_PASSWORD'])

    queues = [Queue(name, connection=conn) for name in listen]
    worker = Worker(queues, connection=conn)
    worker.work()


@app.cli.command()
def format():
    """Runs the yapf and isort formatters over the project."""
    isort = 'isort -rc *.py app/'
    yapf = 'yapf -r -i *.py app/'

    print('Running {}'.format(isort))
    subprocess.call(isort, shell=True)

    print('Running {}'.format(yapf))
    subprocess.call(yapf, shell=True)


@app.cli.command('load-json-book')
@click.argument('file')
def load_json_book(file):
    print("Loading: ", file)
    JsonFileBookLoader(file).load()


@app.cli.command('setup-demo')
def setup_demo():
    """Drop/recreate DB, seed roles + admin, load the demo book with audio."""
    import json
    from app.books.loader import BookLoader
    from app.models.content import TextContent

    # 1. Recreate database
    db.drop_all()
    db.create_all()
    db.session.commit()
    print('Database recreated.')

    # 2. Seed roles + admin user
    setup_general()
    print('Roles and admin user created.')

    # 3. Load the Enchanted Forest demo book
    book_path = os.path.join(os.path.dirname(__file__), 'enchanted_forest.json')
    with open(book_path, 'r') as f:
        book_dict = json.load(f)
    loader = BookLoader(book_dict)
    loader.load()
    book = loader.book
    print(f'Loaded book: {book.name}')

    # 4. Rewrite audio_urls to use the demo/ directory
    #    (The loader sets /static/audio/<book_id>/<file>, but the bundled
    #    files live under /static/audio/demo/<file>.)
    contents = TextContent.query.filter(
        TextContent.audio_url.isnot(None)).all()
    for c in contents:
        filename = c.audio_url.rsplit('/', 1)[-1]
        c.audio_url = f'/static/audio/demo/{filename}'
    db.session.commit()

    # 5. Summary
    from app.models import Book
    from app.models.waypoint import Waypoint
    wp_count = Waypoint.query.filter_by(book_id=book.id).count()
    audio_count = len(contents)
    print(f'Demo ready: 1 book, {wp_count} waypoints, {audio_count} audio files')


if __name__ == '__main__':
    app.run(debug=True)
