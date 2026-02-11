from .. import db

class TextContent(db.Model):
    __tablename__ = 'contents'

    id = db.Column(db.Integer, primary_key=True)
    waypoint_id = db.Column(db.Integer, db.ForeignKey('waypoints.id'))
    waypoint = db.relationship("Waypoint", back_populates="content")
    content = db.Column(db.Text)
    audio_url = db.Column(db.String(500), nullable=True)
    audio_duration = db.Column(db.Float, nullable=True)