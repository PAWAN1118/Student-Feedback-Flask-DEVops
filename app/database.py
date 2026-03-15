import sqlite3
import os
from datetime import datetime

DB_PATH = os.environ.get('DB_PATH', '/data/feedback.db')

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT NOT NULL,
            course       TEXT,
            rating       TEXT,
            message      TEXT NOT NULL,
            submitted_at TEXT DEFAULT (datetime('now'))
        )
    ''')
    conn.commit()
    conn.close()

def add_feedback(name, course, rating, message):
    conn = get_connection()
    conn.execute(
        'INSERT INTO feedback (name, course, rating, message, submitted_at) VALUES (?, ?, ?, ?, ?)',
        (name, course, rating, message, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    conn.commit()
    conn.close()

def get_all_feedback():
    conn = get_connection()
    rows = conn.execute('SELECT * FROM feedback ORDER BY submitted_at DESC').fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_paginated_feedback(page, per_page):
    conn    = get_connection()
    offset  = (page - 1) * per_page
    total   = conn.execute('SELECT COUNT(*) FROM feedback').fetchone()[0]
    rows    = conn.execute(
        'SELECT * FROM feedback ORDER BY submitted_at DESC LIMIT ? OFFSET ?',
        (per_page, offset)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows], total

def get_feedback_by_id(feedback_id):
    conn = get_connection()
    row  = conn.execute('SELECT * FROM feedback WHERE id = ?', (feedback_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def delete_feedback(feedback_id):
    conn = get_connection()
    conn.execute('DELETE FROM feedback WHERE id = ?', (feedback_id,))
    conn.commit()
    conn.close()

def update_feedback(feedback_id, name, course, rating, message):
    conn = get_connection()
    conn.execute(
        'UPDATE feedback SET name=?, course=?, rating=?, message=? WHERE id=?',
        (name, course, rating, message, feedback_id)
    )
    conn.commit()
    conn.close()

def search_feedback(query):
    conn = get_connection()
    q    = f'%{query}%'
    rows = conn.execute(
        '''SELECT * FROM feedback
           WHERE name LIKE ? OR course LIKE ? OR message LIKE ?
           ORDER BY submitted_at DESC''',
        (q, q, q)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_stats():
    conn   = get_connection()
    total  = conn.execute('SELECT COUNT(*) FROM feedback').fetchone()[0]
    avg    = conn.execute(
        "SELECT ROUND(AVG(CAST(rating AS REAL)), 1) FROM feedback WHERE rating != '' AND rating IS NOT NULL"
    ).fetchone()[0]
    dist   = conn.execute(
        "SELECT rating, COUNT(*) as count FROM feedback WHERE rating != '' AND rating IS NOT NULL GROUP BY rating ORDER BY rating"
    ).fetchall()
    recent = conn.execute(
        "SELECT COUNT(*) FROM feedback WHERE submitted_at >= datetime('now', '-7 days')"
    ).fetchone()[0]
    conn.close()
    return {
        'total':        total,
        'avg_rating':   avg or 0,
        'distribution': [dict(r) for r in dist],
        'recent':       recent
    }
