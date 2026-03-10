# 1. Activate virtual environment (Windows syntax)
venv\Scripts\activate

# 2. Install dependencies (if not already installed)
pip install -r requirements.txt

# 3. Initialize database (if guestbook.db doesn't exist)
python -c "from src.database import init_db; init_db()"

# 4. Run the app
python src/app.py

# 5. Cleanup database (remove all entries)
python scripts/cleanup_guestbook.py