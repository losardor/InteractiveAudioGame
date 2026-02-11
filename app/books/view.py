import json
import os

from flask import Blueprint, render_template, flash, abort, redirect, url_for, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.books.forms import NewBookForm, NewWayPoint, UploadBookForm, AudioUploadForm
from app.models import Book, User, Waypoint, Option, EditableHTML
from app import db
from app.books import loader


books = Blueprint('books', __name__)



@books.route('/')
@login_required
def index():
    thebooks = Book.query.all()
    start_wps = {wp.book_id: wp for wp in
                 Waypoint.query.filter_by(start=True).all()}
    return render_template('books/index.html', books=thebooks, start_wps=start_wps)


@books.route('/book/<int:book_id>')
@login_required
def book_info(book_id):
    """view a book page"""
    book = Book.query.filter_by(id=book_id).first()
    if book is None:
        abort(404)
    start_wp = Waypoint.query.filter_by(book_id=book_id, start=True).first()
    return render_template('books/waypoint.html', book=book, start_waypoint=start_wp)

@books.route('/book/<int:book_id>/start')
@login_required
def start_book(book_id):
    """start a new session of the book and display first page"""
    wp = Waypoint.query.filter_by(book_id=book_id, start=True).first()
    if wp is None:
        abort(404)
    return redirect(url_for("books.waypoint",waypoint_id=wp.id))

@books.route('/book/<int:book_id>/play/<int:waypoint_id>')
@login_required
def play_waypoint(book_id, waypoint_id):
    """Audio player page for a waypoint"""
    book = Book.query.filter_by(id=book_id).first()
    if book is None:
        abort(404)
    wp = Waypoint.query.filter_by(id=waypoint_id, book_id=book_id).first()
    if wp is None:
        abort(404)
    options = Option.query.filter_by(sourceWaypoint_id=waypoint_id).all()
    return render_template('books/player.html',
                           book=book,
                           waypoint=wp,
                           text_content=wp.content.content if wp.content else None,
                           audio_url=wp.content.audio_url if wp.content else None,
                           options=options)

@books.route('/waypoint/<int:waypoint_id>')
@login_required
def waypoint(waypoint_id):
    """view a book page"""
    wp = Waypoint.query.filter_by(id=waypoint_id).first()
    options = Option.query.filter_by(sourceWaypoint_id=waypoint_id)
    if wp is None:
        abort(404)
    audio_form = AudioUploadForm()
    return render_template('books/waypoint.html', book=wp.book_of, waypoint=wp, options=options, audio_form=audio_form)

@books.route('/waypoint/<int:waypoint_id>/upload-audio', methods=["POST"])
@login_required
def upload_audio(waypoint_id):
    """Upload an audio file for a waypoint"""
    wp = Waypoint.query.filter_by(id=waypoint_id).first()
    if wp is None:
        abort(404)
    form = AudioUploadForm()
    if form.validate_on_submit():
        f = form.audio_file.data
        filename = secure_filename(f.filename)
        upload_dir = os.path.join(
            current_app.config['AUDIO_UPLOAD_DIR'], str(wp.book_id))
        os.makedirs(upload_dir, exist_ok=True)
        f.save(os.path.join(upload_dir, filename))
        wp.content.audio_url = '/static/audio/{}/{}'.format(wp.book_id, filename)
        db.session.commit()
        flash('Audio uploaded successfully.', 'form-success')
    else:
        flash('Invalid file. Please upload an mp3, ogg, or wav file.', 'form-error')
    return redirect(url_for('books.waypoint', waypoint_id=waypoint_id))

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
        book_dict = json.load(f)
        l = loader.BookLoader(book_dict)
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