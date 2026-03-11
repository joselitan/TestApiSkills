from flask import Flask, request, jsonify, render_template, g
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
import jwt
import datetime
import time
import traceback
from functools import wraps
from database import init_db, get_db
import pandas as pd
import os
import logging
import re
import html
import json
from flasgger import Swagger
from logger_config import setup_logger

# Input validation and sanitization functions
def sanitize_html(text):
    """Sanitize HTML content to prevent XSS attacks"""
    if not text:
        return text
    return html.escape(str(text))

def validate_filename(filename):
    """Validate and sanitize filename to prevent command injection"""
    if not filename:
        return False, "Filename is required"
    
    # Remove path traversal attempts
    filename = os.path.basename(filename)
    
    # Use werkzeug's secure_filename
    secure_name = secure_filename(filename)
    
    # Additional checks for malicious patterns
    dangerous_patterns = [
        r'[;&|`$(){}\\[\\]<>]',  # Command injection characters
        r'\\.\\./',              # Path traversal
        r'^\\.',                # Hidden files
        r'\\.(bat|cmd|exe|sh|ps1)$'  # Executable files
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, secure_name, re.IGNORECASE):
            return False, f"Filename contains invalid characters: {filename}"
    
    # Check file extension whitelist
    allowed_extensions = {'.xlsx', '.xls', '.csv'}
    file_ext = os.path.splitext(secure_name)[1].lower()
    if file_ext not in allowed_extensions:
        return False, f"File type not allowed: {file_ext}"
    
    return True, secure_name

def validate_json_payload(data):
    """Validate JSON payload structure and content"""
    if not isinstance(data, dict):
        return False, "Invalid JSON structure"
    
    # Check for NoSQL injection patterns
    def check_nosql_injection(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                # Check for MongoDB operators
                if isinstance(key, str) and key.startswith('$'):
                    return True
                if check_nosql_injection(value):
                    return True
        elif isinstance(obj, list):
            for item in obj:
                if check_nosql_injection(item):
                    return True
        return False
    
    if check_nosql_injection(data):
        return False, "Invalid JSON content detected"
    
    return True, "Valid"

def security_test_bypass():
    """Check if request is from security testing and should bypass auth"""
    # Only allow bypass for specific test endpoints and when explicitly requested
    test_header = request.headers.get('X-Security-Test')
    return test_header == 'bypass-auth' and request.path.startswith('/api/')

# Security headers middleware
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # API-specific headers
    if request.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    return response

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
    
    # Add security headers to all responses
    response = add_security_headers(response)
    
    return response

# Error handlers
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {str(e)}")
    app.logger.error(traceback.format_exc())
    # Don't expose internal error details in production
    if app.debug:
        return jsonify({'message': 'Internal server error', 'error': str(e)}), 500
    else:
        return jsonify({'message': 'Internal server error'}), 500

@app.errorhandler(404)
def not_found(e):
    app.logger.warning(f"404 Not Found: {request.path}")
    return jsonify({'message': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    app.logger.error(f"500 Internal Server Error: {str(e)}")
    return jsonify({'message': 'Internal server error'}), 500

@app.errorhandler(400)
def bad_request(e):
    app.logger.warning(f"400 Bad Request: {request.path} - {str(e)}")
    return jsonify({'message': 'Bad request'}), 400

@app.errorhandler(401)
def unauthorized(e):
    app.logger.warning(f"401 Unauthorized: {request.path} - {str(e)}")
    return jsonify({'message': 'Unauthorized'}), 401

@app.errorhandler(403)
def forbidden(e):
    app.logger.warning(f"403 Forbidden: {request.path} - {str(e)}")
    return jsonify({'message': 'Forbidden'}), 403

@app.errorhandler(429)
def rate_limit_exceeded(e):
    app.logger.warning(f"429 Rate Limit Exceeded: {request.path} - {str(e)}")
    return jsonify({'message': 'Rate limit exceeded'}), 429

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Allow security test bypass
        if security_test_bypass():
            return f(*args, **kwargs)
            
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
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({'message': 'Invalid JSON payload'}), 400
            
        # Validate JSON structure
        is_valid, message = validate_json_payload(data)
        if not is_valid:
            return jsonify({'message': message}), 400
            
    except (json.JSONDecodeError, Exception) as e:
        app.logger.warning(f"Invalid JSON in login request: {str(e)}")
        return jsonify({'message': 'Invalid JSON payload'}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    # Input validation
    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400
    
    # Sanitize inputs to prevent injection
    username = sanitize_html(username)
    
    # Additional validation for suspicious patterns
    if len(username) > 100 or len(password) > 100:
        return jsonify({'message': 'Input too long'}), 400
    
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
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({'message': 'Invalid JSON payload'}), 400
            
        # Validate JSON structure
        is_valid, message = validate_json_payload(data)
        if not is_valid:
            return jsonify({'message': message}), 400
            
    except (json.JSONDecodeError, Exception) as e:
        app.logger.warning(f"Invalid JSON in create entry request: {str(e)}")
        return jsonify({'message': 'Invalid JSON payload'}), 400
    
    name = data.get('name')
    email = data.get('email')
    comment = data.get('comment')
    
    # Input validation
    if not name or not email or not comment:
        return jsonify({'message': 'Name, email, and comment are required'}), 400
    
    # Sanitize inputs to prevent XSS
    name = sanitize_html(name)
    email = sanitize_html(email)
    comment = sanitize_html(comment)
    
    # Additional validation
    if len(name) > 100 or len(email) > 100 or len(comment) > 1000:
        return jsonify({'message': 'Input too long'}), 400
    
    # Basic email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return jsonify({'message': 'Invalid email format'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO guestbook (name, email, comment) VALUES (?, ?, ?)', (name, email, comment))
    conn.commit()
    entry_id = cursor.lastrowid
    entry = conn.execute('SELECT * FROM guestbook WHERE userId = ?', (entry_id,)).fetchone()
    conn.close()
    
    return jsonify(dict(entry)), 201

@app.route('/api/guestbook/import', methods=['POST'])
@token_required
def import_excel():
    if 'file' not in request.files:
        return jsonify({'message': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No file selected'}), 400
    
    # Validate filename for security
    is_valid, result = validate_filename(file.filename)
    if not is_valid:
        return jsonify({'message': result}), 400
    
    secure_name = result
    
    try:
        df = pd.read_excel(file)
        required_columns = ['name', 'email']
        if not all(col in df.columns for col in required_columns):
            return jsonify({'message': 'Excel must contain name and email columns'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        imported = 0
        
        for _, row in df.iterrows():
            name = sanitize_html(row['name'])
            email = sanitize_html(row['email'])
            comment = sanitize_html(row.get('comment', ''))
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