from flask import Flask, request, jsonify, render_template
from werkzeug.security import check_password_hash
import jwt
import datetime
from functools import wraps
from database import init_db, get_db
import pandas as pd
import os

# Explicitly set the static folder path to avoid directory confusion
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, static_folder=os.path.join(basedir, 'static'))
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            token = token.split()[1] if token.startswith('Bearer ') else token
            jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/guestbook')
def guestbook_page():
    return render_template('guestbook.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    
    if user and check_password_hash(user['password'], password):
        token = jwt.encode({
            'user': username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'token': token})
    
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/guestbook', methods=['POST'])
@token_required
def create_entry():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    comment = data.get('comment')
    
    if not name:
        return jsonify({'message': 'Name is required'}), 400
    if not email:
        return jsonify({'message': 'Email is required'}), 400
    if not comment:
        return jsonify({'message': 'Comment is required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO guestbook (name, email, comment) VALUES (?, ?, ?)', (name, email, comment))
    conn.commit()
    entry_id = cursor.lastrowid
    entry = conn.execute('SELECT * FROM guestbook WHERE userId = ?', (entry_id,)).fetchone()
    conn.close()
    
    return jsonify(dict(entry)), 201

@app.route('/api/guestbook', methods=['GET'])
@token_required
def get_all_entries():
    # 1. Get query parameters with defaults
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)

    # 2. Calculate offset for SQL
    offset = (page - 1) * limit

    conn = get_db()

    # 3. Fetch total count (for frontend paginiation UI)
    total_count = conn.execute('SELECT COUNT(*) FROM guestbook').fetchone()[0]

    # 4. Fetch specific slice of data
    entries = conn.execute(
        'SELECT * FROM guestbook ORDER BY created_at DESC LIMIT ? OFFSET ?', 
        (limit, offset)
    ).fetchall()
    conn.close()
    
    # 5. Return data AND metadata
    return jsonify({
        'data': [dict(entry) for entry in entries],
        'meta': {
            'page': page,
            'limit': limit,
            'total': total_count,
            'pages': (total_count + limit - 1) // limit  # Calculate total pages
        }
    })

@app.route('/api/guestbook/<int:user_id>', methods=['GET'])
@token_required
def get_entry(user_id):
    conn = get_db()
    entry = conn.execute('SELECT * FROM guestbook WHERE userId = ?', (user_id,)).fetchone()
    conn.close()
    
    if entry:
        return jsonify(dict(entry))
    return jsonify({'message': 'Entry not found'}), 404

@app.route('/api/guestbook/<int:user_id>', methods=['PUT'])
@token_required
def update_entry(user_id):
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    comment = data.get('comment')
    
    if not name:
        return jsonify({'message': 'Name is required'}), 400
    if not email:
        return jsonify({'message': 'Email is required'}), 400
    if not comment:
        return jsonify({'message': 'Comment is required'}), 400
    
    conn = get_db()
    conn.execute('UPDATE guestbook SET name = ?, email = ?, comment = ? WHERE userId = ?', 
                 (name, email, comment, user_id))
    conn.commit()
    entry = conn.execute('SELECT * FROM guestbook WHERE userId = ?', (user_id,)).fetchone()
    conn.close()
    
    if entry:
        return jsonify(dict(entry))
    return jsonify({'message': 'Entry not found'}), 404

@app.route('/api/guestbook/<int:user_id>', methods=['DELETE'])
@token_required
def delete_entry(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM guestbook WHERE userId = ?', (user_id,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    
    if deleted:
        return jsonify({'message': 'Entry deleted successfully'})
    return jsonify({'message': 'Entry not found'}), 404

@app.route('/api/guestbook/bulk', methods=['DELETE'])
@token_required
def bulk_delete_entries():
    data = request.get_json()
    ids = data.get('ids', [])
    
    if not ids or not isinstance(ids, list):
        return jsonify({'message': 'IDs array is required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    placeholders = ','.join('?' * len(ids))
    cursor.execute(f'DELETE FROM guestbook WHERE userId IN ({placeholders})', ids)
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    
    return jsonify({'deleted': deleted, 'message': f'{deleted} entries deleted successfully'})

@app.route('/api/guestbook/import', methods=['POST'])
@token_required
def import_excel():
    if 'file' not in request.files:
        return jsonify({'message': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No file selected'}), 400
    
    try:
        df = pd.read_excel(file)
        required_columns = ['name', 'email']
        if not all(col in df.columns for col in required_columns):
            return jsonify({'message': 'Excel must contain name and email columns'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        imported = 0
        
        for _, row in df.iterrows():
            name = row['name']
            email = row['email']
            comment = row.get('comment', '')
            cursor.execute('INSERT INTO guestbook (name, email, comment) VALUES (?, ?, ?)', 
                          (name, email, comment))
            imported += 1
        
        conn.commit()
        conn.close()
        
        return jsonify({'imported': imported, 'message': f'{imported} entries imported successfully'})
    except Exception as e:
        return jsonify({'message': f'Error processing file: {str(e)}'}), 400

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=8080)
