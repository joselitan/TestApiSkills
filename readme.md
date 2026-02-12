# 1. Activate virtual environment (Windows syntax)
venv\Scripts\activate

# 2. Install dependencies (if not already installed)
pip install -r requirements.txt

# 3. Initialize database (if guestbook.db doesn't exist)
python -c "from database import init_db; init_db()"

# 4. Run the app
python app.py