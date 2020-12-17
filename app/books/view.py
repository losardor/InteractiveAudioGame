from flask import Blueprint, render_template, flash
from flask_login import login_required

from app.books.forms import NewBookForm
from app.models import Book, User
from app import db

from app.models import EditableHTML
from flask_login import current_user
from flask import current_app


books = Blueprint('books', __name__)



@books.route('/')
@login_required
def index():
    thebooks = Book.query.all()
    return render_template('books/index.html', books=thebooks)


@books.route('/book/<int:book_id>')
@login_required
def book_info(book_id):
    """view a book page"""
    book = Book.query.filter_by(id=book_id).first()
    if book is None:
        abort(404)
    return render_template('books/waypoint.html', book=book)

@books.route('/book/<int:book_id>/waypoint/<int:waypoint>')
@login_required
def waypoint(book_id, waypoint):
    """view a book page"""
    book = Book.query.filter_by(id=book_id).first()
    if book is None:
        abort(404)
    return render_template('books/waypoint.html', book=book, waypoint=waypoint)




@books.route('/addnew', methods=["GET", "POST"])
@login_required
def addnew():
    """
    Adding a new book
    """
    form = NewBookForm()
    if form.validate_on_submit():
        book = Book(
            name=form.title.data,
            description=form.description.data,
            owner_id=current_user.id)
        db.session.add(book)
        db.session.commit()
        flash('Book {} successfully created'.format(book.name),
                'form-success')
    return render_template('books/new_book.html', form=form)
