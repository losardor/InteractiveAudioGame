from flask import Blueprint, render_template
from flask_login import login_required
from app.models import Book

from app.models import EditableHTML

books = Blueprint('books', __name__)


@books.route('/')
@login_required
def index():
    books = Book.query.all()
    return render_template('books/index.html', books=books)

