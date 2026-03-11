from flask import Flask, request, jsonify, render_template, g
from werkzeug.security import check_password_hash
import jwt
import datetime
import time
import traceback
from functools import wraps
from database import init_db, get_db
import pandas as pd
import os
import logging
from flasgger import Swagger
from logger_config import setup_logger

# Explicitly set the static folder path to avoid directory confusion
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
app = Flask(__name__, 
            static_folder=os.path.join(basedir, 'static'),
            template_folder=os.path.join(basedir, 'templates'))
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'

# Swagger configuration
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Guestbook API",
        "description": "RESTful API for Guestbook application with JWT authentication",
        "version": "1.0.0",
        "contact": {
            "name": "TestApiSkills",
        }
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header using the Bearer scheme. Example: 'Bearer {token}'"
        }
    },
    "security": [
        {"Bearer": []}
    ]
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

# Setup logging
access_logger = setup_logger(app)

# Request logging middleware
@app.before_request
def before_request():
    g.start_time = time.time()
    g.request_id = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')

@app.after_request
def after_request(response):
    if hasattr(g, 'start_time'):
        elapsed = (time.time() - g.start_time) * 1000
        
        # Get user from token if available
        user = 'anonymous'
        token = request.headers.get('Authorization')
        if token:
            try:
                token = token.split()[1] if token.startswith('Bearer ') else token
                payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
                user = payload.get('user', 'unknown')
            except:
                pass
        
        # Log the request
        log_msg = f"{request.method} {request.path} | User: {user} | IP: {request.remote_addr} | Status: {response.status_code} | Time: {elapsed:.0f}ms"
        
        if response.status_code >= 500:
            app.logger.error(log_msg)
        elif response.status_code >= 400:
            app.logger.warning(log_msg)
        else:
            access_logger.info(log_msg)
        
        # Warn on slow requests
        if elapsed > 500:
            app.logger.warning(f"Slow request detected: {request.path} took {elapsed:.0f}ms")
    
    return response

# Error handlers
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {str(e)}")
    app.logger.error(traceback.format_exc())
    return jsonify({'message': 'Internal server error', 'error': str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    app.logger.warning(f"404 Not Found: {request.path}")
    return jsonify({'message': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    app.logger.error(f"500 Internal Server Error: {str(e)}")
    return jsonify({'message': 'Internal server error'}), 500

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
    """
    User login endpoint
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: credentials
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              example: "admin"
            password:
              type: string
              example: "password123"
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            token:
              type: string
              example: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      401:
        description: Invalid credentials
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Invalid credentials"
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    app.logger.info(f"Login attempt for user: {username} from IP: {request.remote_addr}")
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    
    if user and check_password_hash(user['password'], password):
        token = jwt.encode({
            'user': username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        app.logger.info(f"Login successful for user: {username}")
        return jsonify({'token': token})
    
    app.logger.warning(f"Login failed for user: {username} - Invalid credentials")
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/guestbook', methods=['POST'])
@token_required
def create_entry():
    """
    Create a new guestbook entry
    ---
    tags:
      - Guestbook
    security:
      - Bearer: []
    parameters:
      - in: body
        name: entry
        required: true
        schema:
          type: object
          required:
            - name
            - email
            - comment
          properties:
            name:
              type: string
              example: "John Doe"
            email:
              type: string
              example: "john@example.com"
            comment:
              type: string
              example: "Great API!"
    responses:
      201:
        description: Entry created successfully
        schema:
          type: object
          properties:
            userId:
              type: integer
              example: 1
            name:
              type: string
              example: "John Doe"
            email:
              type: string
              example: "john@example.com"
            comment:
              type: string
              example: "Great API!"
            created_at:
              type: string
              example: "2024-03-06 10:30:00"
      400:
        description: Bad request - missing required fields
      401:
        description: Unauthorized - invalid or missing token
    """
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
    """
    Get all guestbook entries with pagination and search
    ---
    tags:
      - Guestbook
    security:
      - Bearer: []
    parameters:
      - in: query
        name: page
        type: integer
        default: 1
        description: Page number
      - in: query
        name: limit
        type: integer
        default: 10
        description: Number of entries per page
      - in: query
        name: search
        type: string
        description: Search term (searches in name, email, and comment)
    responses:
      200:
        description: List of guestbook entries
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                type: object
                properties:
                  userId:
                    type: integer
                  name:
                    type: string
                  email:
                    type: string
                  comment:
                    type: string
                  created_at:
                    type: string
            meta:
              type: object
              properties:
                page:
                  type: integer
                limit:
                  type: integer
                total:
                  type: integer
                pages:
                  type: integer
      401:
        description: Unauthorized
    """
    # 1. Get query parameters with defaults
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    search = request.args.get('search', None, type=str)

    # 2. Calculate offset for SQL
    offset = (page - 1) * limit

    conn = get_db()

    # 3. Build query parts based on search
    base_query = 'FROM guestbook'
    where_clause = ''
    params = []
    if search:
        where_clause = ' WHERE name LIKE ? OR email LIKE ? OR comment LIKE ?'
        search_term = f'%{search}%'
        params.extend([search_term, search_term, search_term])

    # 4. Fetch total count with filter
    count_query = f'SELECT COUNT(*) {base_query}{where_clause}'
    total_count = conn.execute(count_query, params).fetchone()[0]

    # 5. Fetch specific slice of data with filter
    data_query = f'SELECT * {base_query}{where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?'
    query_params = params + [limit, offset]
    entries = conn.execute(data_query, query_params).fetchall()
    conn.close()
    
    # 6. Return data AND metadata
    return jsonify({
        'data': [dict(entry) for entry in entries],
        'meta': {
            'page': page,
            'limit': limit,
            'total': total_count,
            'pages': (total_count + limit - 1) // limit if limit > 0 else 0
        }
    })

@app.route('/api/guestbook/<int:user_id>', methods=['GET'])
@token_required
def get_entry(user_id):
    """
    Get a single guestbook entry by ID
    ---
    tags:
      - Guestbook
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
        description: The entry ID
    responses:
      200:
        description: Guestbook entry found
        schema:
          type: object
          properties:
            userId:
              type: integer
            name:
              type: string
            email:
              type: string
            comment:
              type: string
            created_at:
              type: string
      404:
        description: Entry not found
      401:
        description: Unauthorized
    """
    conn = get_db()
    entry = conn.execute('SELECT * FROM guestbook WHERE userId = ?', (user_id,)).fetchone()
    conn.close()
    
    if entry:
        return jsonify(dict(entry))
    return jsonify({'message': 'Entry not found'}), 404

@app.route('/api/guestbook/<int:user_id>', methods=['PUT'])
@token_required
def update_entry(user_id):
    """
    Update a guestbook entry
    ---
    tags:
      - Guestbook
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
        description: The entry ID to update
      - in: body
        name: entry
        required: true
        schema:
          type: object
          required:
            - name
            - email
            - comment
          properties:
            name:
              type: string
              example: "Jane Doe"
            email:
              type: string
              example: "jane@example.com"
            comment:
              type: string
              example: "Updated comment"
    responses:
      200:
        description: Entry updated successfully
        schema:
          type: object
          properties:
            userId:
              type: integer
            name:
              type: string
            email:
              type: string
            comment:
              type: string
            created_at:
              type: string
      400:
        description: Bad request
      404:
        description: Entry not found
      401:
        description: Unauthorized
    """
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
    """
    Delete a guestbook entry
    ---
    tags:
      - Guestbook
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
        description: The entry ID to delete
    responses:
      200:
        description: Entry deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Entry deleted successfully"
      404:
        description: Entry not found
      401:
        description: Unauthorized
    """
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
    """
    Delete multiple guestbook entries
    ---
    tags:
      - Guestbook
    security:
      - Bearer: []
    parameters:
      - in: body
        name: ids
        required: true
        schema:
          type: object
          required:
            - ids
          properties:
            ids:
              type: array
              items:
                type: integer
              example: [1, 2, 3]
    responses:
      200:
        description: Entries deleted successfully
        schema:
          type: object
          properties:
            deleted:
              type: integer
              example: 3
            message:
              type: string
              example: "3 entries deleted successfully"
      400:
        description: Bad request - IDs array required
      401:
        description: Unauthorized
    """
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

@app.route('/api/guestbook/cleanup', methods=['DELETE'])
@token_required
def cleanup_all_entries():
    """
    Delete ALL guestbook entries (cleanup database)
    ---
    tags:
      - Guestbook
    security:
      - Bearer: []
    parameters:
      - in: query
        name: test_mode
        type: boolean
        default: false
        description: Whether to cleanup test database (true) or production database (false)
    responses:
      200:
        description: All entries deleted successfully
        schema:
          type: object
          properties:
            deleted:
              type: integer
              example: 25
            message:
              type: string
              example: "25 entries deleted successfully"
            database:
              type: string
              example: "production"
      401:
        description: Unauthorized
      500:
        description: Database error
    """
    test_mode = request.args.get('test_mode', 'false').lower() == 'true'
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Count entries before deletion
        count_before = cursor.execute("SELECT COUNT(*) FROM guestbook").fetchone()[0]
        
        if count_before == 0:
            conn.close()
            return jsonify({
                'deleted': 0, 
                'message': 'No entries to delete',
                'database': 'test' if test_mode else 'production'
            })
        
        # Delete all entries
        cursor.execute("DELETE FROM guestbook")
        conn.commit()
        
        # Count after deletion to verify
        count_after = cursor.execute("SELECT COUNT(*) FROM guestbook").fetchone()[0]
        deleted = count_before - count_after
        
        conn.close()
        
        app.logger.info(f"Cleanup completed: {deleted} entries deleted from {'test' if test_mode else 'production'} database")
        
        return jsonify({
            'deleted': deleted,
            'message': f'{deleted} entries deleted successfully',
            'database': 'test' if test_mode else 'production'
        })
        
    except Exception as e:
        app.logger.error(f"Cleanup failed: {str(e)}")
        return jsonify({'message': f'Cleanup failed: {str(e)}'}), 500

@app.route('/api/guestbook/import', methods=['POST'])
@token_required
def import_excel():
    """
    Import guestbook entries from Excel file
    ---
    tags:
      - Guestbook
    security:
      - Bearer: []
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: file
        type: file
        required: true
        description: Excel file with columns 'name', 'email', and optionally 'comment'
    responses:
      200:
        description: Entries imported successfully
        schema:
          type: object
          properties:
            imported:
              type: integer
              example: 5
            message:
              type: string
              example: "5 entries imported successfully"
      400:
        description: Bad request - invalid file or format
      401:
        description: Unauthorized
    """
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
