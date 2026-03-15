import sqlite3
import os
from datetime import datetime

# Database file path — stored in a volume-friendly location
DB_PATH = os.environ.get('DB_PATH', '/data/feedback.db')

def get_connection():
    """Create and return a database connection."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Allows dict-like access to rows
    return conn

def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT    NOT NULL,
            course    TEXT,
            rating    TEXT,
            message   TEXT    NOT NULL,
            submitted_at TEXT DEFAULT (datetime('now'))
        )
    ''')
    conn.commit()
    conn.close()
    print(f"[DB] Database initialized at {DB_PATH}")

def add_feedback(name, course, rating, message):
    """Insert a new feedback record."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO feedback (name, course, rating, message, submitted_at) VALUES (?, ?, ?, ?, ?)',
        (name, course, rating, message, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    conn.commit()
    conn.close()

def get_all_feedback():
    """Retrieve all feedback entries, newest first."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM feedback ORDER BY submitted_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
