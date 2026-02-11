import unittest

from app import create_app, db
from app.models import Book, Role, User
from app.models.waypoint import Waypoint
from app.models.option import Option
from app.models.content import TextContent
from app.books.loader import BookLoader


SIMPLE_BOOK = {
    "name": "Test Book",
    "description": "A test description",
    "waypoints": [
        {
            "id": 1,
            "start": True,
            "content": {"type": "text", "data": "Starting point"},
            "options": [
                {"destinationWaypoint_id": 2, "linkText": "Go to 2"}
            ]
        },
        {
            "id": 2,
            "start": False,
            "content": {"type": "text", "data": "Second waypoint"},
            "options": [
                {"destinationWaypoint_id": 1, "linkText": "Back to 1"}
            ]
        }
    ]
}

BRANCHING_BOOK = {
    "name": "Branching Book",
    "description": "A book with branching paths",
    "waypoints": [
        {
            "id": 1,
            "start": True,
            "content": {"type": "text", "data": "You stand at a crossroads."},
            "options": [
                {"destinationWaypoint_id": 2, "linkText": "Go left"},
                {"destinationWaypoint_id": 3, "linkText": "Go right"}
            ]
        },
        {
            "id": 2,
            "start": False,
            "content": {"type": "text", "data": "You went left."},
            "options": [
                {"destinationWaypoint_id": 1, "linkText": "Go back"}
            ]
        },
        {
            "id": 3,
            "start": False,
            "content": {"type": "text", "data": "You went right."},
            "options": [
                {"destinationWaypoint_id": 1, "linkText": "Go back"}
            ]
        }
    ]
}

NON_TEXT_CONTENT_BOOK = {
    "name": "Non-text Book",
    "description": "A book with non-text content type",
    "waypoints": [
        {
            "id": 1,
            "start": True,
            "content": {"type": "audio", "data": "some_audio_ref"},
            "options": [
                {"destinationWaypoint_id": 2, "linkText": "Next"}
            ]
        },
        {
            "id": 2,
            "start": False,
            "content": {"type": "text", "data": "Normal text"},
            "options": [
                {"destinationWaypoint_id": 1, "linkText": "Back"}
            ]
        }
    ]
}


class BookLoaderTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        u = User(first_name='Test', last_name='Owner',
                 email='owner@example.com', password='password',
                 confirmed=True)
        db.session.add(u)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_load_creates_book(self):
        loader = BookLoader(SIMPLE_BOOK)
        loader.load()
        book = Book.query.filter_by(name='Test Book').first()
        self.assertIsNotNone(book)
        self.assertEqual(book.description, 'A test description')

    def test_load_creates_waypoints(self):
        loader = BookLoader(SIMPLE_BOOK)
        loader.load()
        book = Book.query.filter_by(name='Test Book').first()
        waypoints = Waypoint.query.filter_by(book_id=book.id).all()
        self.assertEqual(len(waypoints), 2)

    def test_start_waypoint_is_marked(self):
        loader = BookLoader(SIMPLE_BOOK)
        loader.load()
        book = Book.query.filter_by(name='Test Book').first()
        start_wps = Waypoint.query.filter_by(book_id=book.id, start=True).all()
        non_start_wps = Waypoint.query.filter_by(book_id=book.id, start=False).all()
        self.assertEqual(len(start_wps), 1)
        self.assertEqual(len(non_start_wps), 1)

    def test_options_link_correct_waypoints(self):
        loader = BookLoader(SIMPLE_BOOK)
        loader.load()
        options = Option.query.all()
        self.assertEqual(len(options), 2)
        source_ids = {o.sourceWaypoint_id for o in options}
        dest_ids = {o.destinationWaypoint_id for o in options}
        wp_ids = {wp.id for wp in Waypoint.query.all()}
        self.assertTrue(source_ids.issubset(wp_ids))
        self.assertTrue(dest_ids.issubset(wp_ids))

    def test_text_content_assigned_to_waypoints(self):
        loader = BookLoader(SIMPLE_BOOK)
        loader.load()
        contents = TextContent.query.all()
        self.assertEqual(len(contents), 2)
        content_texts = {c.content for c in contents}
        self.assertIn('Starting point', content_texts)
        self.assertIn('Second waypoint', content_texts)
        for c in contents:
            self.assertIsNotNone(c.waypoint_id)

    def test_branching_book_loads_correctly(self):
        loader = BookLoader(BRANCHING_BOOK)
        loader.load()
        book = Book.query.filter_by(name='Branching Book').first()
        self.assertIsNotNone(book)
        waypoints = Waypoint.query.filter_by(book_id=book.id).all()
        self.assertEqual(len(waypoints), 3)
        options = Option.query.all()
        self.assertEqual(len(options), 4)
        start_wp = Waypoint.query.filter_by(book_id=book.id, start=True).first()
        start_options = Option.query.filter_by(
            sourceWaypoint_id=start_wp.id).all()
        self.assertEqual(len(start_options), 2)

    def test_non_text_content_creates_null_content(self):
        loader = BookLoader(NON_TEXT_CONTENT_BOOK)
        loader.load()
        contents = TextContent.query.all()
        self.assertEqual(len(contents), 2)
        null_content = [c for c in contents if c.content is None]
        text_content = [c for c in contents if c.content is not None]
        self.assertEqual(len(null_content), 1)
        self.assertEqual(len(text_content), 1)
        self.assertEqual(text_content[0].content, 'Normal text')

    def test_audio_url_none_when_not_in_json(self):
        loader = BookLoader(SIMPLE_BOOK)
        loader.load()
        for tc in TextContent.query.all():
            self.assertIsNone(tc.audio_url)
            self.assertIsNone(tc.audio_duration)
