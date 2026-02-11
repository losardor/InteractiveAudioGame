from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms.fields import (
    StringField,
    SubmitField,
)
from wtforms.validators import (
    InputRequired,
    Length,
)
from wtforms.fields import TextAreaField

from app import db
from app.models import Role, User

class NewBookForm(FlaskForm):
  
    title = StringField(
        'Title', validators=[InputRequired(),
                                  Length(1, 64)])
    description = TextAreaField(
        'Description', validators=[InputRequired(),
                                 Length(1, 256)])

    submit = SubmitField('NewBook')

class UploadBookForm(FlaskForm):
    file = FileField(validators=[FileRequired()])
    submit = SubmitField('Upload')

class NewWayPoint(FlaskForm):
  
    title = StringField(
        'Title', validators=[InputRequired(),
                                  Length(1, 64)])
    description = TextAreaField(
        'Description', validators=[InputRequired(),
                                 Length(1, 256)])

    submit = SubmitField('NewBook')

  
