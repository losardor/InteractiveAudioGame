from .. import db

class Waypoint(db.Model):
    __tablename__ = 'waypoints'

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))
    start = db.Column(db.Boolean)
    content = db.relationship("TextContent", uselist=False, back_populates="waypoint")