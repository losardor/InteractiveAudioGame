from .. import db

class Waypoint(db.Model):
    __tablename__ = 'waypoints'

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))