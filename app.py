from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Get the DATABASE_URL environment variable and adjust for SQLAlchemy's requirements
uri = os.getenv("DATABASE_URL")  # Heroku sets this environment variable automatically
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)  # Correct the URI for SQLAlchemy

# Heroku PostgreSQL database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:tzQVx33j@localhost/andys-notes-app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define models
class Notebook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    notes = db.relationship('Note', backref='notebook', lazy=True, cascade="all, delete-orphan")

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    notebook_id = db.Column(db.Integer, db.ForeignKey('notebook.id'), nullable=False)

# Routes
@app.route('/')
def index():
    notebooks = Notebook.query.all()
    return render_template('index.html', notebooks=notebooks or [])

@app.route('/add_notebook', methods=['POST'])
def add_notebook():
    name = request.form['name']
    if name:
        notebook = Notebook(name=name)
        db.session.add(notebook)
        db.session.commit()
    return redirect(url_for('view_notebook', notebook_id=notebook.id))  # Redirect to the newly created notebook


@app.route('/delete_notebook/<int:id>', methods=['POST'])
def delete_notebook(id):
    notebook = Notebook.query.get_or_404(id)
    db.session.delete(notebook)
    db.session.commit()
    
    # If a notebook is deleted, redirect to the main page since the notebook no longer exists
    return redirect(url_for('index'))


@app.route('/add_note/<int:notebook_id>', methods=['POST'])
def add_note_to_notebook(notebook_id):
    content = request.form['content']
    notebook = Notebook.query.get_or_404(notebook_id)
    if content:
        note = Note(content=content, notebook=notebook)
        db.session.add(note)
        db.session.commit()
    
    # After adding a note, redirect back to the notebook where the note was added
    return redirect(url_for('view_notebook', notebook_id=notebook_id))


@app.route('/delete_note/<int:id>', methods=['POST'])
def delete_note_from_notebook(id):
    note = Note.query.get_or_404(id)
    notebook_id = note.notebook_id  # Save the notebook ID before deleting the note
    db.session.delete(note)
    db.session.commit()

    # After deleting the note, redirect back to the notebook page
    return redirect(url_for('view_notebook', notebook_id=notebook_id))


@app.route('/edit_note/<int:id>', methods=['POST'])
def edit_note(id):
    note = Note.query.get_or_404(id)
    new_content = request.form['content']
    if new_content:
        note.content = new_content
        db.session.commit()

    # After editing the note, redirect back to the notebook where the note belongs
    return redirect(url_for('view_notebook', notebook_id=note.notebook_id))

@app.route('/notebook/<int:notebook_id>')
def view_notebook(notebook_id):
    notebook = Notebook.query.get_or_404(notebook_id)
    notebooks = Notebook.query.all()  # Get all notebooks for the sidebar
    notes = notebook.notes  # Get the notes for the selected notebook
    return render_template('index.html', notebooks=notebooks, selected_notebook=notebook, notes=notes)

if __name__ == '__main__':
    app.run(debug=True)