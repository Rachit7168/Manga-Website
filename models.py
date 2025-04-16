from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

class Manga(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    genre = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    chapters = db.relationship('Chapter', backref='manga', lazy=True)

class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    manga_id = db.Column(db.Integer, db.ForeignKey('manga.id'), nullable=False)
    chapter_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255))
    slug = db.Column(db.String(255), unique=True, nullable=False) # For URL-friendly chapter links
    upload_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    pdf_path = db.Column(db.String(255)) # Path to the PDF file for the chapter
    db.UniqueConstraint('manga_id', 'chapter_number', name='unique_chapter_per_manga')

# We are removing the Page model as we are only dealing with PDFs now
# class Page(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
#     page_number = db.Column(db.Integer, nullable=False)
#     image_path = db.Column(db.String(255), nullable=False)
#     db.UniqueConstraint('chapter_id', 'page_number', name='unique_page_per_chapter')