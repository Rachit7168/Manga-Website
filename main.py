# Standard Library Imports
import os
import shutil
from datetime import datetime
from functools import wraps

# Third-Party Imports
from flask import Flask, render_template, request, redirect, url_for, abort, flash
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from slugify import slugify
from werkzeug.utils import secure_filename
# Local Application Imports
from models import db, Manga, User, Chapter

# Flask Application Initialization
app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///manga.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'rachit1234'  # Replace with a strong, unique secret key
UPLOAD_FOLDER = os.path.join('static', 'chapters')
ALLOWED_EXTENSIONS = {'pdf'}  # Only allow PDF uploads now
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Flask-Login Configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.user_loader(lambda user_id: User.query.get(int(user_id)))
login_manager.login_view = 'login'  # Optional: Redirect to login page for unauthorized access

# Database Initialization
db.init_app(app)


# Helper Functions
def allowed_file(filename):
    """Checks if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def delete_chapter_directory(manga_title, chapter_title):
    """Deletes the directory containing chapter files."""
    chapter_dir = os.path.join(app.config['UPLOAD_FOLDER'], manga_title, chapter_title)
    if os.path.exists(chapter_dir) and os.path.isdir(chapter_dir):
        shutil.rmtree(chapter_dir)

# Custom Decorators
def admin_only(f):
    """Decorator to restrict access to admin users (assuming user ID 1 is admin)."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

# Routes

@app.route('/')
def home():
    """Displays all manga entries on the homepage."""
    mangas = Manga.query.all()
    return render_template('index.html', mangas=mangas, current_user=current_user)

@app.route('/demo')
def demo():
    """Placeholder for a demo page."""
    return render_template('demo.html')

@app.route('/category')
def category():
    """Placeholder for a category view."""
    return render_template('category.html')

@app.route('/logout')
def logout():
    """Logs the current user out."""
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login."""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("No user with that email exists.", "danger")
        elif not check_password_hash(user.password_hash, password):
            flash("Incorrect password.", "danger")
        else:
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for('home'))
    return render_template('login.html', current_user=current_user)

@app.route('/signin', methods=["GET", "POST"])
def signin():
    """Handles user signup."""
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password_hash = generate_password_hash(request.form['password'], method='pbkdf2:sha256', salt_length=8)
        new_user = User(username=username, email=email, password_hash=password_hash)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))
    return render_template("signup.html", current_user=current_user)

@app.route('/add', methods=['GET', 'POST'])
@admin_only
def add_manga():
    """Handles adding new manga entries."""
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        genre = request.form['genre']
        rating = float(request.form['rating'])
        status = request.form['status']
        description = request.form['description']
        image_url = request.form['image_url']
        new_manga = Manga(title=title, author=author, genre=genre, rating=rating, status=status, description=description, image_url=image_url)
        db.session.add(new_manga)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('add_manga.html', current_user=current_user)

@app.route('/delete/<int:manga_id>', methods=['POST'])
@admin_only
def delete_manga(manga_id):
    """Deletes a manga entry and its associated chapters and pages."""
    manga = Manga.query.get_or_404(manga_id)
    chapters_to_delete = Chapter.query.filter_by(manga_id=manga_id).all()
    for chapter in chapters_to_delete:
        delete_chapter_directory(manga.title, chapter.title)
        # We are no longer deleting pages as we won't create them
        db.session.delete(chapter)
    db.session.delete(manga)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/edit/<int:manga_id>', methods=['GET', 'POST'])
@admin_only
def edit_manga(manga_id):
    """Handles editing existing manga entries."""
    manga = Manga.query.get_or_404(manga_id)
    if request.method == 'POST':
        manga.title = request.form['title']
        manga.author = request.form['author']
        manga.genre = request.form['genre']
        manga.rating = float(request.form['rating'])
        manga.status = request.form['status']
        manga.description = request.form['description']
        manga.image_url = request.form['image_url']
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit_manga.html', manga=manga, current_user=current_user)

@app.route('/manga/<int:manga_id>')
def view_manga(manga_id):
    """Displays the details of a specific manga and its chapters."""
    manga = Manga.query.get_or_404(manga_id)
    chapters = Chapter.query.filter_by(manga_id=manga_id).order_by(Chapter.chapter_number).all()
    return render_template('m_detail.html', manga=manga, chapters=chapters, current_user=current_user)

@app.route('/manga/<int:manga_id>/chapter/<string:chapter_slug>')
def read_chapter(manga_id, chapter_slug):
    manga = Manga.query.get_or_404(manga_id)
    chapter = Chapter.query.filter_by(manga_id=manga.id, slug=chapter_slug).first_or_404()

    pdf_file_path = None

    if chapter.pdf_path:
        pdf_file_path = url_for('static', filename=os.path.join('chapters', manga.title, chapter.title, chapter.pdf_path))
        print(f"Generated PDF Path: {pdf_file_path}")  # Debugging

    return render_template('read.html', manga=manga, chapter=chapter, pdf_path=pdf_file_path, current_user=current_user)


@app.route('/admin/manga/<int:manga_id>/upload_chapter', methods=['GET', 'POST'])
@admin_only
def upload_chapter(manga_id):
    """Handles uploading new chapters (accepts PDF files)."""
    manga = Manga.query.get_or_404(manga_id)
    if request.method == 'POST':
        chapter_title = request.form.get('title')
        chapter_number = request.form.get('chapter_number')
        pdf_file = request.files.get('pdf_file')  # Changed 'pages' to 'pdf_file'

        if not chapter_title or not pdf_file:
            flash("Please provide a chapter title and a PDF file.", "danger")
            return redirect(request.url)

        if not allowed_file(pdf_file.filename):
            flash("Invalid file type. Only PDF files are allowed.", "danger")
            return redirect(request.url)

        chapter_slug = slugify(chapter_title)
        if Chapter.query.filter_by(manga_id=manga.id, slug=chapter_slug).first():
            flash(f"Chapter with title '{chapter_title}' already exists for this manga.", "danger")
            return redirect(request.url)

        chapter = Chapter(manga_id=manga.id, title=chapter_title,
                          chapter_number=int(chapter_number) if chapter_number else None,
                          slug=chapter_slug, upload_date=datetime.utcnow())
        db.session.add(chapter)
        db.session.commit()

        chapter_dir = os.path.join(app.config['UPLOAD_FOLDER'], manga.title, chapter_title)
        os.makedirs(chapter_dir, exist_ok=True)

        pdf_filename = secure_filename(pdf_file.filename)
        pdf_path_on_server = os.path.join(chapter_dir, pdf_filename)
        try:
            pdf_file.save(pdf_path_on_server)
            chapter.pdf_path = pdf_filename  # Store only the filename in the database
            db.session.commit()
            flash(f"Chapter '{chapter_title}' uploaded successfully.", "success")
            return redirect(url_for('view_manga', manga_id=manga.id))
        except Exception as e:
            flash(f"Error saving PDF file: {e}", "error")
            db.session.delete(chapter)
            db.session.commit()
            delete_chapter_directory(manga.title, chapter_title)
            return redirect(request.url)

    return render_template('upload.html', manga=manga, current_user=current_user) # Changed template name

@app.route('/admin/manga/<int:manga_id>/chapter/<int:chapter_id>/delete', methods=['POST'])
@admin_only
def delete_chapter(manga_id, chapter_id):
    """Deletes a specific chapter and its associated PDF."""
    manga = Manga.query.get_or_404(manga_id)
    chapter = Chapter.query.get_or_404(chapter_id)
    if chapter.manga_id != manga.id:
        abort(403)
    delete_chapter_directory(manga.title, chapter.title)
    db.session.delete(chapter)
    db.session.commit()
    flash(f"Chapter '{chapter.title}' deleted successfully.", "success")
    return redirect(url_for('view_manga', manga_id=manga.id))

@app.route("/about")
def about():
    """Displays the about page."""
    return render_template("about.html", current_user=current_user)

# Run the App
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)