# Importing necessary modules from Flask and models
from flask import Flask, render_template, request, redirect, url_for , abort , flash
from models import db, Manga , User
from werkzeug.security import generate_password_hash , check_password_hash
from flask_login import login_user, LoginManager, current_user, logout_user , login_required
from functools import wraps


# Creating Flask application instance
app = Flask(__name__)

# Configuring database URI and disabling modification tracking
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///manga.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#Flask Login
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initializing the database with the app

db.init_app(app)


# Create an admin-only decorator
def admin_only(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function



# Home route - displays all manga entries
@app.route('/')
def home():
    mangas = Manga.query.all()  # Retrieve all manga records from the database
    return render_template('index.html', mangas=mangas , current_user = current_user)

@app.route('/demo')
def demo():
    return render_template('demo.html')

# Category route - placeholder for category view
@app.route('/category')
def category():
    return render_template('category.html')

@app.route('/logout')
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for('home'))

# Login page route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check if user exists
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("No user with that email exists.", "danger")
        elif not check_password_hash(user.password_hash, password):
            flash("Incorrect password.", "danger")
        else:
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for('home'))

    return render_template('login.html' , current_user =current_user)

# Signup page route
@app.route('/signin', methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password_hash = generate_password_hash(
            request.form['password'],
            method='pbkdf2:sha256',
            salt_length=8
        )

        new_user = User(username=username,
                        email=email,
                        password_hash=password_hash)
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)  # ✅ Use new_user here
        return redirect(url_for('home'))  # or wherever your homepage is

    return render_template("signup.html", current_user=current_user)


# Add manga route - handles both displaying the form and processing the form submission
@app.route('/add', methods=['GET', 'POST'])
@admin_only
def add_manga():
    if request.method == 'POST':
        # Retrieve form data
        title = request.form['title']
        author = request.form['author']
        genre = request.form['genre']
        rating = float(request.form['rating'])
        status = request.form['status']
        description = request.form['description']
        image_url = request.form['image_url']
        
        # Create a new Manga object and save it to the database
        new_manga = Manga(
            title=title,
            author=author,
            genre=genre,
            rating=rating,
            status=status,
            description=description,
            image_url=image_url
        )
        db.session.add(new_manga)
        db.session.commit()
        
        return redirect(url_for('home'))

    return render_template('add_manga.html' , current_user =current_user)


# Delete manga route - deletes the manga with the given ID
@app.route('/delete/<int:manga_id>', methods=['POST'])
@admin_only
def delete_manga(manga_id):
    manga = Manga.query.get_or_404(manga_id)  # Get manga or return 404 if not found
    db.session.delete(manga)
    db.session.commit()
    return redirect(url_for('home'))

# Edit manga route - handles both displaying the edit form and processing the updates
@app.route('/edit/<int:manga_id>', methods=['GET', 'POST'])
@admin_only
def edit_manga(manga_id):
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

    return render_template('edit_manga.html', manga=manga , current_user =current_user)


# View manga detail route - shows a single manga's details
@app.route('/manga/<int:manga_id>')
def view_manga(manga_id):
    manga = Manga.query.get_or_404(manga_id)  # Get manga or return 404 if not found
    return render_template('m_detail.html', manga=manga , current_user =current_user)

@app.route("/about")
def about():
    return render_template("about.html")

# Run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
# Run the Flask app in debug mode
