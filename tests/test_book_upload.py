import json
import unittest

from app import create_app, db
from app.models import Book, Role, User
from app.models.waypoint import Waypoint
from app.models.option import Option
from app.models.content import TextContent
from app.books.loader import BookLoader
from config import Config


ENCHANTED_FOREST_PATH = 'enchanted_forest.json'


def load_enchanted_forest():
    with open(ENCHANTED_FOREST_PATH, 'r') as f:
        return json.load(f)


class BookUploadTestCase(unittest.TestCase):
    """Tests for loading the Enchanted Forest book via CLI loader and web upload."""

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.admin = User(
            first_name='Admin', last_name='Account',
            email=Config.ADMIN_EMAIL, password='password', confirmed=True)
        db.session.add(self.admin)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_cli_loader_creates_book(self):
        """BookLoader creates the book with correct name and description."""
        book_dict = load_enchanted_forest()
        loader = BookLoader(book_dict)
        loader.load()
        book = Book.query.filter_by(name='The Enchanted Forest').first()
        self.assertIsNotNone(book)
        self.assertIn('branching adventure', book.description)

    def test_cli_loader_creates_eight_waypoints(self):
        book_dict = load_enchanted_forest()
        BookLoader(book_dict).load()
        book = Book.query.filter_by(name='The Enchanted Forest').first()
        wps = Waypoint.query.filter_by(book_id=book.id).all()
        self.assertEqual(len(wps), 8)

    def test_cli_loader_start_waypoint(self):
        """Exactly one waypoint has start=True, the rest have start=False."""
        book_dict = load_enchanted_forest()
        BookLoader(book_dict).load()
        book = Book.query.filter_by(name='The Enchanted Forest').first()
        starts = Waypoint.query.filter_by(book_id=book.id, start=True).all()
        non_starts = Waypoint.query.filter_by(book_id=book.id, start=False).all()
        self.assertEqual(len(starts), 1)
        self.assertEqual(len(non_starts), 7)

    def test_cli_loader_creates_options(self):
        """8 options total: WP1(2), WP2(2), WP3(2), WP5(2), WP4/6/7/8(0 each)."""
        book_dict = load_enchanted_forest()
        BookLoader(book_dict).load()
        options = Option.query.all()
        self.assertEqual(len(options), 8)

    def test_cli_loader_creates_text_content(self):
        """Each waypoint gets a TextContent record."""
        book_dict = load_enchanted_forest()
        BookLoader(book_dict).load()
        contents = TextContent.query.all()
        self.assertEqual(len(contents), 8)
        for c in contents:
            self.assertIsNotNone(c.content)
            self.assertIsNotNone(c.waypoint_id)

    def test_cli_loader_sets_audio_urls(self):
        """All 8 waypoints have audio in the JSON; loader sets audio_url for each."""
        book_dict = load_enchanted_forest()
        BookLoader(book_dict).load()
        book = Book.query.filter_by(name='The Enchanted Forest').first()
        contents = TextContent.query.all()
        audio_contents = [c for c in contents if c.audio_url is not None]
        self.assertEqual(len(audio_contents), 8)
        for c in audio_contents:
            self.assertTrue(
                c.audio_url.startswith(f'/static/audio/{book.id}/'))

    def test_web_upload_creates_book(self):
        """Uploading enchanted_forest.json via /books/uploadnew creates the book."""
        client = self.app.test_client()
        client.post('/account/login', data={
            'email': Config.ADMIN_EMAIL, 'password': 'password'})
        with open(ENCHANTED_FOREST_PATH, 'rb') as f:
            r = client.post('/books/uploadnew',
                            data={'file': (f, 'enchanted_forest.json')},
                            content_type='multipart/form-data')
        self.assertIn(r.status_code, (200, 302))
        book = Book.query.filter_by(name='The Enchanted Forest').first()
        self.assertIsNotNone(book)
        self.assertEqual(
            Waypoint.query.filter_by(book_id=book.id).count(), 8)
        self.assertEqual(TextContent.query.count(), 8)
        self.assertEqual(Option.query.count(), 8)

    def test_web_upload_does_not_500(self):
        """The upload route must not return a 500 error."""
        client = self.app.test_client()
        client.post('/account/login', data={
            'email': Config.ADMIN_EMAIL, 'password': 'password'})
        with open(ENCHANTED_FOREST_PATH, 'rb') as f:
            r = client.post('/books/uploadnew',
                            data={'file': (f, 'enchanted_forest.json')},
                            content_type='multipart/form-data')
        self.assertLess(r.status_code, 500)


class BookNavigationTestCase(unittest.TestCase):
    """Tests that a loaded book is navigable through the player and waypoint routes."""

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.admin = User(
            first_name='Admin', last_name='Account',
            email=Config.ADMIN_EMAIL, password='password', confirmed=True)
        db.session.add(self.admin)
        db.session.commit()

        # Load the book
        book_dict = load_enchanted_forest()
        BookLoader(book_dict).load()
        self.book = Book.query.filter_by(name='The Enchanted Forest').first()

        # Build a mapping from JSON waypoint id to DB waypoint id
        # by matching on the start flag and content text
        self.wp_map = {}
        for wp_json in book_dict['waypoints']:
            for wp_db in Waypoint.query.filter_by(book_id=self.book.id).all():
                if wp_db.content and wp_db.content.content and \
                   wp_json['content']['data'][:30] in wp_db.content.content:
                    self.wp_map[wp_json['id']] = wp_db.id
                    break

        self.client = self.app.test_client()
        self.client.post('/account/login', data={
            'email': Config.ADMIN_EMAIL, 'password': 'password'})

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_start_waypoint_loads(self):
        """The start waypoint renders successfully via the play route."""
        start_wp = Waypoint.query.filter_by(
            book_id=self.book.id, start=True).first()
        r = self.client.get(
            f'/books/book/{self.book.id}/play/{start_wp.id}')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'ancient forest', r.data)

    def test_follow_option_to_destination(self):
        """Following an option from the start loads the destination waypoint."""
        start_wp = Waypoint.query.filter_by(
            book_id=self.book.id, start=True).first()
        option = Option.query.filter_by(
            sourceWaypoint_id=start_wp.id).first()
        r = self.client.get(
            f'/books/book/{self.book.id}/play/{option.destinationWaypoint_id}')
        self.assertEqual(r.status_code, 200)

    def test_dead_end_waypoint_loads(self):
        """A waypoint with no options (dead end) renders 'The End'."""
        # WP4 in JSON is the cave ending
        wp4_id = self.wp_map.get(4)
        self.assertIsNotNone(wp4_id)
        r = self.client.get(f'/books/book/{self.book.id}/play/{wp4_id}')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'The End', r.data)

    def test_full_path_wp1_wp2_wp5_wp7(self):
        """Navigate a complete path: WP1 -> WP2 -> WP5 -> WP7 (village ending)."""
        wp1 = self.wp_map[1]
        wp2 = self.wp_map[2]
        wp5 = self.wp_map[5]
        wp7 = self.wp_map[7]

        r = self.client.get(f'/books/book/{self.book.id}/play/{wp1}')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'ancient forest', r.data)

        r = self.client.get(f'/books/book/{self.book.id}/play/{wp2}')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'dark path', r.data)

        r = self.client.get(f'/books/book/{self.book.id}/play/{wp5}')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'river', r.data)

        r = self.client.get(f'/books/book/{self.book.id}/play/{wp7}')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'village', r.data)
        self.assertIn(b'The End', r.data)

    def test_waypoint_view_route_also_works(self):
        """The legacy /waypoint/<id> route still works for loaded waypoints."""
        start_wp = Waypoint.query.filter_by(
            book_id=self.book.id, start=True).first()
        r = self.client.get(f'/books/waypoint/{start_wp.id}')
        self.assertEqual(r.status_code, 200)

    def test_book_info_page_has_listen_button(self):
        """The book info page shows a Listen button linking to the player."""
        r = self.client.get(f'/books/book/{self.book.id}')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Listen', r.data)
        self.assertIn(b'/play/', r.data)
