from .. import db

class Option(db.Model):
    __tablename__ = 'options'

    id = db.Column(db.Integer, primary_key=True)
    sourceWaypoint_id = db.Column(db.Integer, db.ForeignKey('waypoints.id'))
    destinationWaypoint_id = db.Column(db.Integer, db.ForeignKey('waypoints.id'))
    linkText = db.Column(db.Text, unique=True)