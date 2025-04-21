# Standard Library Imports
import os  # Provides functions for interacting with the operating system (e.g., file paths).
import shutil  # Offers high-level file operations (e.g., copying, moving, deleting).
from datetime import datetime  # Used for working with dates and times (e.g., recording upload times).
from functools import wraps  # A decorator for preserving function metadata when wrapping functions.
import re  # Provides regular expression operations for pattern matching in strings.

# Third-Party Imports
from flask import Flask, render_template, request, redirect, url_for, abort, flash  # Core Flask functionalities.
from flask_login import login_user, LoginManager, current_user, logout_user, login_required  # For user authentication.
from werkzeug.security import generate_password_hash, check_password_hash  # For secure password handling.
from werkzeug.utils import secure_filename  # For safely handling uploaded filenames.
from slugify import slugify  # For generating URL-friendly slugs from strings.

# Local Application Imports
from models import db, Manga, User, Chapter  # Import database object and models from models.py.


# Flask Application Initialization
app = Flask(__name__)  # Creates the Flask application instance.

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///manga.db'  # Sets the database URI (using SQLite).
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disables SQLAlchemy modification tracking.
app.secret_key = 'rachit1234'  # Secret key for session management (replace with a strong, unique key).
UPLOAD_FOLDER = os.path.join('static', 'chapters')  # Defines the directory for uploaded chapter files.
ALLOWED_EXTENSIONS = {'pdf'}  # Sets the allowed file extensions for uploads.
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # Configures the upload folder in the Flask app.

# Flask-Login Configuration
login_manager = LoginManager()  # Creates a LoginManager instance.
login_manager.init_app(app)  # Initializes Flask-Login with the Flask application.
login_manager.user_loader(lambda user_id: User.query.get(int(user_id)))  # Function to load a user from the session.
login_manager.login_view = 'login'  # Endpoint to redirect unauthenticated users trying to access protected views.

# Database Initialization
db.init_app(app)  # Initializes the Flask-SQLAlchemy extension with the Flask application.

# Helper Functions
def sanitize_filename(name):
    """Removes or replaces unsafe characters from a filename."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()  # Uses regex to remove or replace problematic characters.

def allowed_file(filename):
    """Checks if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS  # Checks for a dot and if the extension is in the allowed set.

def delete_chapter_directory(manga_title, chapter_title):
    """Deletes the directory containing chapter files."""
    chapter_dir = os.path.join(app.config['UPLOAD_FOLDER'], manga_title, chapter_title)  # Constructs the path to the chapter directory.
    if os.path.exists(chapter_dir) and os.path.isdir(chapter_dir):  # Checks if the directory exists and is a directory.
        shutil.rmtree(chapter_dir)  # Recursively deletes the directory and its contents.

# Custom Decorators
def admin_only(f):
    """Decorator to restrict access to admin users (assuming user ID 1 is admin)."""
    @wraps(f)  # Preserves the original function's metadata.
    @login_required  # Ensures the user is logged in before accessing the view.
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:  # Checks if the current user's ID is not 1 (admin).
            abort(403)  # Returns a 403 Forbidden error if the user is not admin.
        return f(*args, **kwargs)  # Calls the original function if the user is admin.
    return decorated_function  # Returns the decorated function.


# Routes
@app.route('/')
def home():
    """Displays all manga entries on the homepage."""
    mangas = Manga.query.all()  # Retrieves all manga entries from the database.
    return render_template('index.html', mangas=mangas, current_user=current_user)  # Renders the homepage with manga data and current user.

@app.route('/demo')
def demo():
    """Placeholder for a demo page."""
    return render_template('demo.html')  # Renders the demo page.

@app.route('/category')
def category():
    """Placeholder for a category view."""
    return render_template('category.html')  # Renders the category page.

@app.route('/logout')
def logout():
    """Logs the current user out."""
    logout_user()  # Logs out the current user.
    flash("Logged out successfully.", "success")  # Flashes a success message.
    return redirect(url_for('home'))  # Redirects the user to the homepage.

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login."""
    if request.method == 'POST':  # Checks if the request method is POST (form submission).
        email = request.form['email']  # Retrieves the email from the login form.
        password = request.form['password']  # Retrieves the password from the login form.
        user = User.query.filter_by(email=email).first()  # Queries the database for a user with the given email.

        if not user:  # If no user with that email exists.
            flash("No user with that email exists.", "danger")  # Flashes an error message.
        elif not check_password_hash(user.password_hash, password):  # If the entered password doesn't match the stored hash.
            flash("Incorrect password.", "danger")  # Flashes an error message.
        else:  # If the user exists and the password is correct.
            login_user(user)  # Logs in the user.
            flash("Logged in successfully!", "success")  # Flashes a success message.
            return redirect(url_for('home'))  # Redirects the user to the homepage.
    return render_template('login.html', current_user=current_user)  # Renders the login form (for GET requests).

@app.route('/signin', methods=["GET", "POST"])
def signin():
    """Handles user signup."""
    if request.method == "POST":  # Checks if the request method is POST (form submission).
        username = request.form['username']  # Retrieves the username from the signup form.
        email = request.form['email']  # Retrieves the email from the signup form.
        password_hash = generate_password_hash(request.form['password'], method='pbkdf2:sha256', salt_length=8)  # Hashes the password securely.
        new_user = User(username=username, email=email, password_hash=password_hash)  # Creates a new User object.
        db.session.add(new_user)  # Adds the new user to the database session.
        db.session.commit()  # Commits the changes to the database.
        login_user(new_user)  # Logs in the newly signed-up user.
        return redirect(url_for('home'))  # Redirects the user to the homepage.
    return render_template("signup.html", current_user=current_user)  # Renders the signup form (for GET requests).

@app.route('/add', methods=['GET', 'POST'])
@admin_only  # Only accessible by admin users.
def add_manga():
    """Handles adding new manga entries."""
    if request.method == 'POST':  # Checks if the request method is POST (form submission).
        title = request.form['title']  # Retrieves the title from the add manga form.
        author = request.form['author']  # Retrieves the author from the add manga form.
        genre = request.form['genre']  # Retrieves the genre from the add manga form.
        rating = float(request.form['rating'])  # Retrieves and converts the rating to a float.
        status = request.form['status']  # Retrieves the status from the add manga form.
        description = request.form['description']  # Retrieves the description from the add manga form.
        image_url = request.form['image_url']  # Retrieves the image URL from the add manga form.
        new_manga = Manga(title=title, author=author, genre=genre, rating=rating, status=status, description=description, image_url=image_url)  # Creates a new Manga object.
        db.session.add(new_manga)  # Adds the new manga to the database session.
        db.session.commit()  # Commits the changes to the database.
        return redirect(url_for('home'))  # Redirects the user to the homepage.
    return render_template('add_manga.html', current_user=current_user)  # Renders the add manga form (for GET requests).

@app.route('/delete/<int:manga_id>', methods=['POST'])
@admin_only  # Only accessible by admin users.
def delete_manga(manga_id):
    """Deletes a manga entry and its associated chapters and pages."""
    manga = Manga.query.get_or_404(manga_id)  # Retrieves the manga to delete, or returns 404 if not found.
    chapters_to_delete = Chapter.query.filter_by(manga_id=manga_id).all()  # Retrieves all chapters associated with the manga.
    for chapter in chapters_to_delete:  # Iterates through the chapters to be deleted.
        delete_chapter_directory(manga.title, chapter.title)  # Deletes the directory containing the chapter files.
        db.session.delete(chapter)  # Deletes the chapter from the database session.
    db.session.delete(manga)  # Deletes the manga from the database session.
    db.session.commit()  # Commits the changes to the database.
    return redirect(url_for('home'))  # Redirects the user to the homepage.

@app.route('/edit/<int:manga_id>', methods=['GET', 'POST'])
@admin_only  # Only accessible by admin users.
def edit_manga(manga_id):
    """Handles editing existing manga entries."""
    manga = Manga.query.get_or_404(manga_id)  # Retrieves the manga to edit, or returns 404 if not found.
    if request.method == 'POST':  # Checks if the request method is POST (form submission).
        manga.title = request.form['title']  # Updates the manga title.
        manga.author = request.form['author']  # Updates the manga author.
        manga.genre = request.form['genre']  # Updates the manga genre.
        manga.rating = float(request.form['rating'])  # Updates the manga rating.
        manga.status = request.form['status']  # Updates the manga status.
        manga.description = request.form['description']  # Updates the manga description.
        manga.image_url = request.form['image_url']  # Updates the manga image URL.
        db.session.commit()  # Commits the changes to the database.
        return redirect(url_for('home'))  # Redirects the user to the homepage.
    return render_template('edit_manga.html', manga=manga, current_user=current_user)  # Renders the edit manga form (for GET requests).

@app.route('/manga/<int:manga_id>')
def view_manga(manga_id):
    """Displays the details of a specific manga and its chapters."""
    manga = Manga.query.get_or_404(manga_id)  # Retrieves the manga to view, or returns 404 if not found.
    chapters = Chapter.query.filter_by(manga_id=manga_id).order_by(Chapter.chapter_number).all()  # Retrieves all chapters for the manga, ordered by chapter number.
    return render_template('m_detail.html', manga=manga, chapters=chapters, current_user=current_user)  # Renders the manga details page.

@app.route('/manga/<int:manga_id>/chapter/<string:chapter_slug>')
def read_chapter(manga_id, chapter_slug):
    """Displays a specific chapter of a manga."""
    manga = Manga.query.get_or_404(manga_id)  # Retrieves the manga, or returns 404 if not found.
    chapter = Chapter.query.filter_by(manga_id=manga.id, slug=chapter_slug).first_or_404()  # Retrieves the chapter based on manga ID and slug, or returns 404.
    pdf_file_path = None  # Initializes the PDF file path.
    if chapter.pdf_path:  # Checks if a PDF path is associated with the chapter.
        pdf_file_path = url_for('static', filename=f"chapters/{manga.title}/{chapter.title}/{chapter.pdf_path}")  # Constructs the URL for the PDF file.
    return render_template('read.html', manga=manga, chapter=chapter, pdf_path=pdf_file_path, current_user=current_user)  # Renders the read chapter page.

@app.route('/admin/manga/<int:manga_id>/upload_chapter', methods=['GET', 'POST'])
@admin_only  # Only accessible by admin users.
def upload_chapter(manga_id):
    """Handles uploading new chapters (accepts PDF files)."""
    manga = Manga.query.get_or_404(manga_id)  # Retrieves the manga to upload a chapter to.
    if request.method == 'POST':  # Checks if the request method is POST (form submission).
        chapter_title = request.form.get('title')  # Retrieves the chapter title from the form.
        chapter_number = request.form.get('chapter_number')  # Retrieves the chapter number from the form.
        pdf_file = request.files.get('pdf_file')  # Retrieves the uploaded PDF file.

        if not chapter_title or not pdf_file:  # Checks if both title and file are provided.
            flash("Please provide a chapter title and a PDF file.", "danger")  # Flashes an error message.
            return redirect(request.url)  # Redirects back to the upload form.

        if not allowed_file(pdf_file.filename):  # Checks if the uploaded file has an allowed extension.
            flash("Invalid file type. Only PDF files are allowed.", "danger")  # Flashes an error message.
            return redirect(request.url)  # Redirects back to the upload form.

        chapter_slug = slugify(chapter_title)  # Generates a URL-friendly slug from the chapter title.
        if Chapter.query.filter_by(manga_id=manga.id, slug=chapter_slug).first():  # Checks if a chapter with the same slug already exists.
            flash(f"Chapter with title '{chapter_title}' already exists for this manga.", "danger")  # Flashes an error message.
            return redirect(request.url)  # Redirects back to the upload form.

        chapter = Chapter(manga_id=manga.id, title=chapter_title,  # Creates a new Chapter object.
                        chapter_number=int(chapter_number) if chapter_number else None,
                        slug=chapter_slug, upload_date=datetime.utcnow())
        db.session.add(chapter)  # Adds the new chapter to the database session.
        db.session.commit()  # Commits the changes to the database to get the chapter ID.

        chapter_dir = os.path.join(app.config['UPLOAD_FOLDER'], manga.title, chapter_title)  # Constructs the directory path for the chapter's files.
        os.makedirs(chapter_dir, exist_ok=True)  # Creates the directory if it doesn't exist.

        pdf_filename = secure_filename(pdf_file.filename)  # Safely secures the uploaded filename.
        pdf_path_on_server = os.path.join(chapter_dir, pdf_filename)  # Constructs the full path to save the PDF.
        try:
            pdf_file.save(pdf_path_on_server)  # Saves the uploaded PDF file to the server.
            chapter.pdf_path = pdf_filename  # Stores the filename of the PDF in the database.
            db.session.commit()  # Commits the changes to the database.
            flash(f"Chapter '{chapter_title}' uploaded successfully.", "success")  # Flashes a success message.
            return redirect(url_for('view_manga', manga_id=manga.id))  # Redirects to the manga's detail page.
        except Exception as e:  # Handles potential errors during file saving.
            flash(f"Error saving PDF file: {e}", "error")  # Flashes an error message.
            db.session.delete(chapter)  # If saving fails, delete the chapter record from the database.
            db.session.commit()  # Commit the deletion of the chapter record.
            delete_chapter_directory(manga.title, chapter_title)  # Delete the partially created chapter directory.
            return redirect(request.url)  # Redirect back to the upload form.

    return render_template('upload.html', manga=manga, current_user=current_user)  # Renders the upload form (for GET requests).

@app.route('/admin/manga/<int:manga_id>/chapter/<int:chapter_id>/delete', methods=['POST'])
@admin_only  # Only accessible by admin users.
def delete_chapter(manga_id, chapter_id):
    """Deletes a specific chapter and its associated PDF."""
    manga = Manga.query.get_or_404(manga_id)  # Retrieves the manga, or returns 404 if not found.
    chapter = Chapter.query.get_or_404(chapter_id)  # Retrieves the chapter to delete, or returns 404 if not found.
    if chapter.manga_id != manga.id:  # Checks if the chapter belongs to the specified manga.
        abort(403)  # Returns a 403 Forbidden error if the chapter doesn't belong to the manga.
    delete_chapter_directory(manga.title, chapter.title)  # Deletes the directory containing the chapter files.
    db.session.delete(chapter)  # Deletes the chapter from the database session.
    db.session.commit()  # Commits the changes to the database.
    flash(f"Chapter '{chapter.title}' deleted successfully.", "success")  # Flashes a success message.
    return redirect(url_for('view_manga', manga_id=manga.id))  # Redirects to the manga's detail page.

@app.route("/about")
def about():
    """Displays the about page."""
    return render_template("about.html", current_user=current_user)  # Renders the about page.

# Run the App
if __name__ == '__main__':
    with app.app_context():  # Creates an application context for database operations.
        db.create_all()  # Creates the database tables if they don't exist.
    app.run(debug=True)  # Runs the Flask development server with debugging enabled.
