from .. import db

class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    description = db.Column(db.Text, unique=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    