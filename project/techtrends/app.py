import sys
import sqlite3
import logging
from logging.config import dictConfig

from flask import (
    Flask, 
    jsonify, 
    json, 
    render_template, 
    request,
    url_for, 
    redirect, 
    flash
)
from werkzeug.exceptions import abort

# Function to get a database connection.
# This function connects to database with the name `database.db`

def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    global db_connection_count 
    db_connection_count += 1
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://sys.stderr',
        'formatter': 'default'
    }},
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi']
    }
})

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'
db_connection_count = 1

# Define the main route of the web application 
@app.route('/')
def index():
    global db_connection_count 
    db_connection_count += 1
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      app.logger.info('Non-existing article is accessed.')  
      return render_template('404.html'), 404
    else:
      title = post['title']  
      app.logger.info(f'Article "{title}" retrieved!')
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    global db_connection_count 
    db_connection_count += 1
    app.logger.info('About Us page is retrieved!')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    global db_connection_count 
    db_connection_count += 1
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            app.logger.info(f'Article "{title}" is created')
            return redirect(url_for('index'))
    
    return render_template('create.html')

@app.route('/healthz')
def status():
    response  = app.response_class(
        response = json.dumps({'result': 'OK -healthy'}),
        status = 200,
        mimetype = 'application/json'
        )
    return response

@app.route('/metrics')
def metrics():
    query = """Select count(*) From posts"""
    connection = get_db_connection()
    post_count = connection.execute(query).fetchone()[0]
    global db_connection_count 
    db_connection_count += 1
    response = app.response_class(
        response = json.dumps(
            {'db_connection_count': db_connection_count, 
            'post_count': post_count}),
        status = 200,
        mimetype = 'application/json'
    )
    return response

# start the application on port 3111
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app.run(host='0.0.0.0', port='3111')
