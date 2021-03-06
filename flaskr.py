# imports
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from contextlib import closing

# config
DATABASE = '/tmp/flaskr.db'
DEBUG = True
SECRET_KEY = str(os.urandom(24))
USERNAME = 'admin'
PASSWORD = 'default'

# app
app = Flask(__name__)
app.config.from_object(__name__)


def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        
def fetch_entry(post_id):
        cur = g.db.execute('select title, text, id from entries where id=?', [post_id])
        e = cur.fetchone()
        return dict(title=e[0], text=e[1], id=e[2])
        
@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route('/')
def show_entries():
    cur = g.db.execute('select title, text, id from entries order by id desc')
    entries = [dict(title=row[0], text=row[1], id=row[2]) for row in cur.fetchall()]
    return render_template('show_entries.html', entries=entries)

@app.route('/entry/<int:post_id>/', methods=['GET'])
def entry(post_id):
    entry = fetch_entry(post_id)
    return render_template('entry.html', entry=entry)

@app.route('/add/', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    g.db.execute('insert into entries (title, text) values (?, ?)', [request.form['title'], request.form['text']])
    g.db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))

@app.route('/edit/<int:post_id>/', methods=['GET', 'POST'])
def edit(post_id):
    if not session.get('logged_in'):
        flash("You must be logged in")
        return redirect(url_for('entry', post_id=post_id))
    if request.method == 'POST':
        g.db.execute('update entries set title = ?, text = ? where id=?', [request.form['title'], request.form['text'], post_id])
        g.db.commit()
        flash("Post was successfully supdated")
        return redirect(url_for('entry', post_id=post_id))
    else:
        entry = fetch_entry(post_id)
        return render_template('edit.html', entry=entry)

@app.route('/delete/<int:post_id>/', methods=['POST'])
def delete(post_id):
    if not session.get('logged_in'):
        abort(401)
    else:
        g.db.execute('delete from entries where id=?', [post_id])
        g.db.commit()
        flash("Post successfully deleted")
        return redirect(url_for('show_entries'))

@app.route('/login/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/logout/')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

if __name__ == '__main__':
    app.run()
