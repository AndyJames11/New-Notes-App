from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  # Import Flask-Migrate
import os

app = Flask(__name__)

# Secret key for session management
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key_for_dev')

# Get the DATABASE_URL environment variable and adjust for SQLAlchemy's requirements
uri = os.getenv("DATABASE_URL")  # Heroku sets this environment variable automatically
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)  # Correct the URI for SQLAlchemy

# Heroku PostgreSQL database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:tzQVx33j@localhost/andys-notes-app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Set up Flask-Migrate

# Define models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    notebooks = db.relationship('Notebook', backref='user', lazy=True)

class Notebook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notes = db.relationship('Note', backref='notebook', lazy=True, cascade="all, delete-orphan")

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    notebook_id = db.Column(db.Integer, db.ForeignKey('notebook.id'), nullable=False)
    
# Routes
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    notebooks = Notebook.query.filter_by(user_id=user_id).all()
    return render_template('index.html', notebooks=notebooks)

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id
            session['user_name'] = user.name
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password')
            return redirect(url_for('login'))
    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Account creation route
@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with that email already exists.')
            return redirect(url_for('create_account'))
        user = User(name=name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully! Please log in.')
        return redirect(url_for('login'))
    return render_template('create_account.html')

@app.route('/add_notebook', methods=['POST'])
def add_notebook():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    name = request.form['name']
    if name:
        notebook = Notebook(name=name, user_id=session['user_id'])
        db.session.add(notebook)
        db.session.commit()
    return redirect(url_for('view_notebook', notebook_id=notebook.id))  # Redirect to the newly created notebook


@app.route('/delete_notebook/<int:id>', methods=['POST'])
def delete_notebook(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    notebook = Notebook.query.get_or_404(id)
    if notebook.user_id != session['user_id']:
        flash("You don't have permission to delete this notebook")
        return redirect(url_for('index'))
    
    db.session.delete(notebook)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/add_note/<int:notebook_id>', methods=['POST'])
def add_note_to_notebook(notebook_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    content = request.form['content']
    notebook = Notebook.query.get_or_404(notebook_id)
    if notebook.user_id != session['user_id']:
        flash("You don't have permission to add a note to this notebook")
        return redirect(url_for('index'))

    if content:
        note = Note(content=content, notebook=notebook)
        db.session.add(note)
        db.session.commit()
    
    # After adding a note, redirect back to the notebook where the note was added
    return redirect(url_for('view_notebook', notebook_id=notebook_id))

@app.route('/delete_note/<int:id>', methods=['POST'])
def delete_note_from_notebook(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    note = Note.query.get_or_404(id)
    notebook_id = note.notebook_id
    if note.notebook.user_id != session['user_id']:
        flash("You don't have permission to delete this note")
        return redirect(url_for('index'))

    db.session.delete(note)
    db.session.commit()

    # After deleting the note, redirect back to the notebook page
    return redirect(url_for('view_notebook', notebook_id=notebook_id))

@app.route('/edit_note/<int:id>', methods=['POST'])
def edit_note(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    note = Note.query.get_or_404(id)
    if note.notebook.user_id != session['user_id']:
        flash("You don't have permission to edit this note")
        return redirect(url_for('index'))

    new_content = request.form['content']
    if new_content:
        note.content = new_content
        db.session.commit()

    # After editing the note, redirect back to the notebook where the note belongs
    return redirect(url_for('view_notebook', notebook_id=note.notebook_id))

@app.route('/notebook/<int:notebook_id>')
def view_notebook(notebook_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    notebook = Notebook.query.get_or_404(notebook_id)
    if notebook.user_id != session['user_id']:
        flash("You don't have permission to view this notebook")
        return redirect(url_for('index'))

    notes = notebook.notes # Get all the notes from the notebook
    notebooks = Notebook.query.filter_by(user_id=session['user_id']).all() # Show all notebooks
    return render_template('index.html', notebooks=notebooks, selected_notebook=notebook, notes=notes)

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
