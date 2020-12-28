from .. import db

class TextContent(db.Model):
    __tablename__ = 'contents'

    id = db.Column(db.Integer, primary_key=True)
    waypoint_id = db.Column(db.Integer, db.ForeignKey('waypoints.id'))
    content = db.Columns(db.Text)