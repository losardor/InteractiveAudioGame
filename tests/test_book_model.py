import unittest

from app import create_app, db
from app.models import Book, Role, User
from app.models.waypoint import Waypoint
from app.models.option import Option
from app.models.content import TextContent


class BookModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        u = User(first_name='Test', last_name='User',
                 email='test@example.com', password='password',
                 confirmed=True)
        db.session.add(u)
        db.session.commit()
        self.user = u

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_book(self):
        b = Book(name='Test Book', description='A description',
                 owner_id=self.user.id)
        db.session.add(b)
        db.session.commit()
        self.assertIsNotNone(b.id)
        self.assertEqual(b.name, 'Test Book')
        self.assertEqual(b.description, 'A description')
        self.assertEqual(b.owner_id, self.user.id)

    def test_waypoint_linked_to_book(self):
        b = Book(name='WP Book', description='desc', owner_id=self.user.id)
        db.session.add(b)
        db.session.flush()
        wp = Waypoint(book_id=b.id, start=False)
        db.session.add(wp)
        db.session.commit()
        self.assertEqual(wp.book_id, b.id)
        self.assertIn(wp, b.wp_rel.all())

    def test_waypoint_start_flag(self):
        b = Book(name='Start Book', description='desc', owner_id=self.user.id)
        db.session.add(b)
        db.session.flush()
        wp_start = Waypoint(book_id=b.id, start=True)
        wp_other = Waypoint(book_id=b.id, start=False)
        db.session.add_all([wp_start, wp_other])
        db.session.commit()
        self.assertTrue(wp_start.start)
        self.assertFalse(wp_other.start)

    def test_option_links_waypoints(self):
        b = Book(name='Opt Book', description='desc', owner_id=self.user.id)
        db.session.add(b)
        db.session.flush()
        wp1 = Waypoint(book_id=b.id, start=True)
        wp2 = Waypoint(book_id=b.id, start=False)
        db.session.add_all([wp1, wp2])
        db.session.flush()
        opt = Option(sourceWaypoint_id=wp1.id,
                     destinationWaypoint_id=wp2.id,
                     linkText='Go to chapter 2')
        db.session.add(opt)
        db.session.commit()
        self.assertEqual(opt.sourceWaypoint_id, wp1.id)
        self.assertEqual(opt.destinationWaypoint_id, wp2.id)
        self.assertEqual(opt.linkText, 'Go to chapter 2')

    def test_text_content_linked_to_waypoint(self):
        b = Book(name='Cnt Book', description='desc', owner_id=self.user.id)
        db.session.add(b)
        db.session.flush()
        wp = Waypoint(book_id=b.id, start=True)
        db.session.add(wp)
        db.session.flush()
        tc = TextContent(waypoint_id=wp.id, content='Once upon a time...')
        db.session.add(tc)
        db.session.commit()
        self.assertEqual(tc.waypoint_id, wp.id)
        self.assertEqual(tc.content, 'Once upon a time...')
        self.assertEqual(wp.content, tc)

    def test_text_content_audio_fields_default_to_none(self):
        b = Book(name='Audio Book', description='desc', owner_id=self.user.id)
        db.session.add(b)
        db.session.flush()
        wp = Waypoint(book_id=b.id, start=True)
        db.session.add(wp)
        db.session.flush()
        tc = TextContent(waypoint_id=wp.id, content='Some text')
        db.session.add(tc)
        db.session.commit()
        self.assertIsNone(tc.audio_url)
        self.assertIsNone(tc.audio_duration)

    def test_text_content_can_store_audio_fields(self):
        b = Book(name='Audio Book 2', description='desc2',
                 owner_id=self.user.id)
        db.session.add(b)
        db.session.flush()
        wp = Waypoint(book_id=b.id, start=True)
        db.session.add(wp)
        db.session.flush()
        tc = TextContent(waypoint_id=wp.id, content='Narrated text',
                         audio_url='/static/audio/chapter1.mp3',
                         audio_duration=125.5)
        db.session.add(tc)
        db.session.commit()
        fetched = db.session.get(TextContent, tc.id)
        self.assertEqual(fetched.audio_url, '/static/audio/chapter1.mp3')
        self.assertEqual(fetched.audio_duration, 125.5)
