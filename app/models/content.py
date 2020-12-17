from .. import db

class Content(db.Model):
    __tablename__ = 'contents'

    id = db.Column(db.Integer, primary_key=True)
    waypoint_id = db.Column(db.Integer, db.ForeignKey('waypoints.id'))