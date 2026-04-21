"""
NutriAI — SQLite Database Layer
All queries use parameterized placeholders to prevent SQL injection.
"""

import sqlite3
import os
import re
import json
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nutriai.db")


def get_connection():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create tables and indexes if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL DEFAULT 'User',
            health_goal TEXT NOT NULL DEFAULT 'maintenance',
            daily_calorie_target INTEGER DEFAULT 2000,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS meal_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 1,
            food_name TEXT NOT NULL,
            meal_type TEXT NOT NULL CHECK(meal_type IN ('breakfast','lunch','dinner','snack')),
            calories REAL DEFAULT 0,
            protein_g REAL DEFAULT 0,
            fat_g REAL DEFAULT 0,
            carbs_g REAL DEFAULT 0,
            sugar_g REAL DEFAULT 0,
            fiber_g REAL DEFAULT 0,
            serving_size TEXT DEFAULT '100g',
            mood TEXT DEFAULT '',
            hunger_level TEXT DEFAULT '',
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS api_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_key TEXT NOT NULL UNIQUE,
            response_json TEXT NOT NULL,
            cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_meal_logs_user ON meal_logs(user_id);
        CREATE INDEX IF NOT EXISTS idx_meal_logs_date ON meal_logs(logged_at);
        CREATE INDEX IF NOT EXISTS idx_api_cache_query ON api_cache(query_key);
    """)

    # Insert default user if none exists
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO users (name, health_goal) VALUES (?, ?)",
            ("User", "maintenance")
        )

    conn.commit()
    conn.close()


# ── Input Sanitization ──────────────────────────────────────────────

def sanitize_text(text, max_length=200):
    """Remove HTML tags, limit length, strip dangerous characters."""
    if not isinstance(text, str):
        return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove null bytes
    text = text.replace('\x00', '')
    # Strip and truncate
    text = text.strip()[:max_length]
    return text


def validate_meal_type(meal_type):
    """Validate meal type against allowed values."""
    allowed = {'breakfast', 'lunch', 'dinner', 'snack'}
    if meal_type not in allowed:
        return 'snack'
    return meal_type


def validate_number(value, min_val=0, max_val=99999):
    """Validate and clamp a numeric value."""
    try:
        value = float(value)
        return max(min_val, min(value, max_val))
    except (TypeError, ValueError):
        return 0.0


# ── CRUD Operations ─────────────────────────────────────────────────

def log_meal(user_id, food_name, meal_type, nutrition, mood="", hunger=""):
    """Log a meal entry with sanitized inputs."""
    conn = get_connection()
    cursor = conn.cursor()

    food_name = sanitize_text(food_name, 300)
    meal_type = validate_meal_type(meal_type)
    mood = sanitize_text(mood, 50)
    hunger = sanitize_text(hunger, 50)

    cursor.execute("""
        INSERT INTO meal_logs 
            (user_id, food_name, meal_type, calories, protein_g, fat_g, 
             carbs_g, sugar_g, fiber_g, serving_size, mood, hunger_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        int(user_id),
        food_name,
        meal_type,
        validate_number(nutrition.get('calories', 0)),
        validate_number(nutrition.get('protein', 0)),
        validate_number(nutrition.get('fat', 0)),
        validate_number(nutrition.get('carbs', 0)),
        validate_number(nutrition.get('sugar', 0)),
        validate_number(nutrition.get('fiber', 0)),
        sanitize_text(nutrition.get('serving_size', '100g'), 50),
        mood,
        hunger
    ))

    conn.commit()
    meal_id = cursor.lastrowid
    conn.close()
    return meal_id


def get_meal_history(user_id, days=7):
    """Get meal history for the last N days."""
    conn = get_connection()
    cursor = conn.cursor()

    since = (datetime.now() - timedelta(days=days)).isoformat()
    cursor.execute("""
        SELECT id, food_name, meal_type, calories, protein_g, fat_g,
               carbs_g, sugar_g, fiber_g, serving_size, mood, hunger_level, logged_at
        FROM meal_logs
        WHERE user_id = ? AND logged_at >= ?
        ORDER BY logged_at DESC
    """, (int(user_id), since))

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_daily_totals(user_id, days=7):
    """Get aggregated daily nutrition totals."""
    conn = get_connection()
    cursor = conn.cursor()

    since = (datetime.now() - timedelta(days=days)).isoformat()
    cursor.execute("""
        SELECT DATE(logged_at) as date,
               SUM(calories) as total_cal,
               SUM(protein_g) as total_protein,
               SUM(fat_g) as total_fat,
               SUM(carbs_g) as total_carbs,
               SUM(sugar_g) as total_sugar,
               SUM(fiber_g) as total_fiber,
               COUNT(*) as meal_count
        FROM meal_logs
        WHERE user_id = ? AND logged_at >= ?
        GROUP BY DATE(logged_at)
        ORDER BY date ASC
    """, (int(user_id), since))

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_user(user_id=1):
    """Get user profile."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (int(user_id),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_user_goal(user_id, goal, calorie_target=2000):
    """Update user health goal."""
    allowed_goals = {'weight-loss', 'muscle-gain', 'maintenance', 'diabetes-control', 'heart-health'}
    if goal not in allowed_goals:
        goal = 'maintenance'

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET health_goal = ?, daily_calorie_target = ? WHERE id = ?",
        (goal, int(calorie_target), int(user_id))
    )
    conn.commit()
    conn.close()


# ── Cache Operations ─────────────────────────────────────────────────

def get_cached_response(query_key):
    """Get cached API response if it's less than 24 hours old."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT response_json, cached_at FROM api_cache WHERE query_key = ?",
        (query_key,)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        cached_at = datetime.fromisoformat(row['cached_at'])
        if datetime.now() - cached_at < timedelta(hours=24):
            return json.loads(row['response_json'])
    return None


def set_cached_response(query_key, response_data):
    """Cache an API response."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO api_cache (query_key, response_json, cached_at)
        VALUES (?, ?, ?)
    """, (query_key, json.dumps(response_data), datetime.now().isoformat()))
    conn.commit()
    conn.close()


# Initialize on import
init_db()
