# Importing necessary modules from Flask and models
from flask import Flask, render_template, request, redirect, url_for
from models import db, Manga

# Creating Flask application instance
app = Flask(__name__)

# Configuring database URI and disabling modification tracking
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///manga.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initializing the database with the app
db.init_app(app)

# Home route - displays all manga entries
@app.route('/')
def home():
    mangas = Manga.query.all()  # Retrieve all manga records from the database
    return render_template('index.html', mangas=mangas)

# Category route - placeholder for category view
@app.route('/category')
def category():
    return render_template('category.html')

# Login page route
@app.route('/login')
def login():
    return render_template('login.html')

# Signup page route
@app.route('/signin')
def signin():
    return render_template("signup.html")

# Add manga route - handles both displaying the form and processing the form submission
@app.route('/add', methods=['GET', 'POST'])
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

    return render_template('add_manga.html')


# Delete manga route - deletes the manga with the given ID
@app.route('/delete/<int:manga_id>', methods=['POST'])
def delete_manga(manga_id):
    manga = Manga.query.get_or_404(manga_id)  # Get manga or return 404 if not found
    db.session.delete(manga)
    db.session.commit()
    return redirect(url_for('home'))

# Edit manga route - handles both displaying the edit form and processing the updates
@app.route('/edit/<int:manga_id>', methods=['GET', 'POST'])
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

    return render_template('edit_manga.html', manga=manga)


# View manga detail route - shows a single manga's details
@app.route('/manga/<int:manga_id>')
def view_manga(manga_id):
    manga = Manga.query.get_or_404(manga_id)  # Get manga or return 404 if not found
    return render_template('m_detail.html', manga=manga)

@app.route("/about")
def about():
    return render_template("about.html")

# Run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
# Run the Flask app in debug mode
