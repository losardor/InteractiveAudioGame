from flask import Blueprint, render_template, flash, abort, redirect, url_for, request
from flask_login import login_required

from app.books.forms import NewBookForm, NewWayPoint, UploadBookForm
from app.models import Book, User, Waypoint, Option
from app import db

from app.models import EditableHTML
from flask_login import current_user
from flask import current_app
from app.books import loader


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

@books.route('/book/<int:book_id>/start')
@login_required
def start_book(book_id):
    """start a new session of the book and display first page"""
    wp = Waypoint.query.filter_by(book_id=book_id, start=True).first()
    if wp is None:
        abort(404)
    return redirect(url_for("books.waypoint",waypoint_id=wp.id))

@books.route('/waypoint/<int:waypoint_id>')
@login_required
def waypoint(waypoint_id):
    """view a book page"""
    wp = Waypoint.query.filter_by(id=waypoint_id).first()
    options = Option.query.filter_by(sourceWaypoint_id=waypoint_id)
    if wp is None:
        abort(404)
    return render_template('books/waypoint.html', book=wp.book_of, waypoint=wp, options=options)

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

@books.route('/uploadnew', methods=["GET", "POST"])
@login_required
def uploadnew():
    """
    Uploading a new book
    """
    form = UploadBookForm()
    if form.validate_on_submit():
        f = form.file.data
        l = loader.JsonFileBookLoader(f)
        l.load()
        flash('Book {} successfully created'.format(l.book.name), 'form-success')
    return render_template('books/upload_book.html', form=form)

@books.route('/book/<int:book_id>/add_point', methods=["GET", "POST"])
@login_required
def addnewwp(book_id):
    """
    Adding a new waypoint
    """
    form = NewWayPoint()
    if form.validate_on_submit():
        wp = Waypoint(book_id=book_id)
        db.session.add(wp)
        db.session.commit()
        flash('wp {} successfully created'.format(wp.id),
                'form-success')
    return render_template('books/new_waypoint.html', form=form)