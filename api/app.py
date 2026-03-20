from flask import Flask, jsonify, request
import psycopg2, os
from datetime import datetime

app = Flask(__name__)

# ---- DATABASE CONNECTION ----
def get_db():
    return psycopg2.connect(os.getenv('DATABASE_URL'))

# ---- CREATE TABLE ON STARTUP ----
def setup():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

setup()

# ---- HEALTH CHECK ----
@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'time': str(datetime.now())
    })

# ---- GET ALL POSTS ----
@app.route('/api/posts', methods=['GET'])
def get_posts():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT * FROM posts
        ORDER BY created_at DESC
    ''')
    posts = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([{
        'id': p[0],
        'title': p[1],
        'content': p[2],
        'author': p[3],
        'created_at': str(p[4])
    } for p in posts])

# ---- GET SINGLE POST ----
@app.route('/api/posts/<int:id>', methods=['GET'])
def get_post(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM posts WHERE id = %s', (id,))
    post = cur.fetchone()
    cur.close()
    conn.close()
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    return jsonify({
        'id': post[0],
        'title': post[1],
        'content': post[2],
        'author': post[3],
        'created_at': str(post[4])
    })

# ---- CREATE A POST ----
@app.route('/api/posts', methods=['POST'])
def create_post():
    data = request.json
    title   = data.get('title')
    content = data.get('content')
    author  = data.get('author')

    # Basic validation
    if not title or not content or not author:
        return jsonify({
            'error': 'title, content and author are required'
        }), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO posts (title, content, author)
        VALUES (%s, %s, %s)
        RETURNING *
    ''', (title, content, author))
    post = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({
        'id': post[0],
        'title': post[1],
        'content': post[2],
        'author': post[3],
        'created_at': str(post[4])
    }), 201

# ---- DELETE A POST ----
@app.route('/api/posts/<int:id>', methods=['DELETE'])
def delete_post(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        'DELETE FROM posts WHERE id = %s RETURNING id', (id,)
    )
    deleted = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if not deleted:
        return jsonify({'error': 'Post not found'}), 404
    return jsonify({
        'message': f'Post {id} deleted successfully'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)