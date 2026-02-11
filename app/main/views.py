from flask import Blueprint, render_template

from app.models import Book, EditableHTML, Waypoint

main = Blueprint('main', __name__)


@main.route('/')
def index():
    featured_book = Book.query.first()
    featured_start_wp = None
    if featured_book:
        featured_start_wp = Waypoint.query.filter_by(
            book_id=featured_book.id, start=True).first()
    return render_template(
        'main/index.html',
        featured_book=featured_book,
        featured_start_wp=featured_start_wp,
    )


@main.route('/about')
def about():
    editable_html_obj = EditableHTML.get_editable_html('about')
    return render_template(
        'main/about.html', editable_html_obj=editable_html_obj)

