from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Get the DATABASE_URL environment variable and adjust for SQLAlchemy's requirements
uri = os.getenv("DATABASE_URL")  # Heroku sets this environment variable automatically
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)  # Correct the URI for SQLAlchemy

# Heroku PostgreSQL database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = uri or 'postgresql://localhost/yourdbname'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define models
class Notebook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    notes = db.relationship('Note', backref='notebook', lazy=True)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    notebook_id = db.Column(db.Integer, db.ForeignKey('notebook.id'), nullable=False)

# Routes
@app.route('/')
def index():
    notebooks = Notebook.query.all()
    return render_template('index.html', notebooks=notebooks)

@app.route('/add_notebook', methods=['POST'])
def add_notebook():
    name = request.form['name']
    if name:
        notebook = Notebook(name=name)
        db.session.add(notebook)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete_notebook/<int:id>', methods=['POST'])
def delete_notebook(id):
    notebook = Notebook.query.get_or_404(id)
    db.session.delete(notebook)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/add_note/<int:notebook_id>', methods=['POST'])
def add_note_to_notebook(notebook_id):
    content = request.form['content']
    notebook = Notebook.query.get_or_404(notebook_id)
    note = Note(content=content, notebook=notebook)
    db.session.add(note)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete_note/<int:id>', methods=['POST'])
def delete_note_from_notebook(id):
    note = Note.query.get_or_404(id)
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
