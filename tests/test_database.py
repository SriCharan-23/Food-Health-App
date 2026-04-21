"""
Tests for database.py — schema, CRUD, sanitization, and caching.
"""

import sys
import os
import sqlite3
import pytest

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db


@pytest.fixture(autouse=True)
def use_temp_db(tmp_path, monkeypatch):
    """Use a temporary database for every test."""
    test_db = str(tmp_path / "test_nutriai.db")
    monkeypatch.setattr(db, "DB_PATH", test_db)
    db.init_db()
    yield test_db


# ── Schema Tests ───────────────────────────────────────────────────

class TestSchema:
    def test_tables_created(self, use_temp_db):
        conn = sqlite3.connect(use_temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        assert "users" in tables
        assert "meal_logs" in tables
        assert "api_cache" in tables

    def test_default_user_created(self):
        user = db.get_user(1)
        assert user is not None
        assert user["name"] == "User"
        assert user["health_goal"] == "maintenance"

    def test_indexes_exist(self, use_temp_db):
        conn = sqlite3.connect(use_temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        conn.close()
        assert "idx_meal_logs_user" in indexes
        assert "idx_meal_logs_date" in indexes
        assert "idx_api_cache_query" in indexes


# ── Sanitization Tests ─────────────────────────────────────────────

class TestSanitization:
    def test_sanitize_removes_html(self):
        assert db.sanitize_text("<script>alert('xss')</script>hello") == "alert('xss')hello"

    def test_sanitize_truncates(self):
        long_text = "a" * 500
        result = db.sanitize_text(long_text, max_length=100)
        assert len(result) == 100

    def test_sanitize_strips_whitespace(self):
        assert db.sanitize_text("  hello  ") == "hello"

    def test_sanitize_removes_null_bytes(self):
        assert db.sanitize_text("hel\x00lo") == "hello"

    def test_sanitize_non_string(self):
        assert db.sanitize_text(123) == ""
        assert db.sanitize_text(None) == ""

    def test_validate_meal_type_valid(self):
        assert db.validate_meal_type("breakfast") == "breakfast"
        assert db.validate_meal_type("lunch") == "lunch"
        assert db.validate_meal_type("dinner") == "dinner"
        assert db.validate_meal_type("snack") == "snack"

    def test_validate_meal_type_invalid(self):
        assert db.validate_meal_type("brunch") == "snack"
        assert db.validate_meal_type("") == "snack"
        assert db.validate_meal_type("DROP TABLE") == "snack"

    def test_validate_number_valid(self):
        assert db.validate_number(42) == 42.0
        assert db.validate_number("99.5") == 99.5

    def test_validate_number_clamps(self):
        assert db.validate_number(-10) == 0.0
        assert db.validate_number(999999) == 99999.0

    def test_validate_number_invalid(self):
        assert db.validate_number("not_a_number") == 0.0
        assert db.validate_number(None) == 0.0


# ── Meal Logging Tests ─────────────────────────────────────────────

class TestMealLogging:
    def test_log_meal_returns_id(self):
        meal_id = db.log_meal(1, "Banana", "breakfast", {"calories": 89, "protein": 1.1})
        assert isinstance(meal_id, int)
        assert meal_id > 0

    def test_log_meal_sanitizes_input(self):
        meal_id = db.log_meal(1, "<b>Evil Food</b>", "lunch", {"calories": 100})
        history = db.get_meal_history(1, 1)
        found = [m for m in history if m["id"] == meal_id]
        assert len(found) == 1
        assert "<b>" not in found[0]["food_name"]

    def test_log_meal_invalid_type_defaults(self):
        meal_id = db.log_meal(1, "Apple", "brunch", {"calories": 52})
        history = db.get_meal_history(1, 1)
        found = [m for m in history if m["id"] == meal_id]
        assert found[0]["meal_type"] == "snack"

    def test_get_meal_history(self):
        db.log_meal(1, "Rice", "lunch", {"calories": 130, "protein": 2.7})
        db.log_meal(1, "Dal", "lunch", {"calories": 120, "protein": 8})
        history = db.get_meal_history(1, 7)
        assert len(history) >= 2

    def test_get_meal_history_empty(self):
        history = db.get_meal_history(999, 7)
        assert history == []

    def test_log_meal_with_mood_and_hunger(self):
        meal_id = db.log_meal(1, "Chocolate", "snack",
                              {"calories": 535, "sugar": 52}, mood="stressed", hunger="not-hungry")
        history = db.get_meal_history(1, 1)
        found = [m for m in history if m["id"] == meal_id]
        assert found[0]["mood"] == "stressed"
        assert found[0]["hunger_level"] == "not-hungry"


# ── Daily Totals Tests ─────────────────────────────────────────────

class TestDailyTotals:
    def test_daily_totals_aggregation(self):
        db.log_meal(1, "Oatmeal", "breakfast", {"calories": 68, "protein": 2.4, "sugar": 0.5})
        db.log_meal(1, "Chicken", "lunch", {"calories": 165, "protein": 31, "sugar": 0})
        totals = db.get_daily_totals(1, 1)
        assert len(totals) >= 1
        today = totals[-1]
        assert today["total_cal"] >= 233
        assert today["meal_count"] >= 2

    def test_daily_totals_empty(self):
        totals = db.get_daily_totals(999, 7)
        assert totals == []


# ── User Tests ─────────────────────────────────────────────────────

class TestUser:
    def test_update_goal(self):
        db.update_user_goal(1, "weight-loss", 1500)
        user = db.get_user(1)
        assert user["health_goal"] == "weight-loss"
        assert user["daily_calorie_target"] == 1500

    def test_update_goal_invalid_defaults(self):
        db.update_user_goal(1, "be-awesome")
        user = db.get_user(1)
        assert user["health_goal"] == "maintenance"

    def test_get_nonexistent_user(self):
        user = db.get_user(9999)
        assert user is None


# ── Cache Tests ────────────────────────────────────────────────────

class TestCache:
    def test_set_and_get_cache(self):
        data = [{"name": "Banana", "calories": 89}]
        db.set_cached_response("test:banana", data)
        cached = db.get_cached_response("test:banana")
        assert cached is not None
        assert cached[0]["name"] == "Banana"

    def test_cache_miss(self):
        cached = db.get_cached_response("nonexistent:key")
        assert cached is None

    def test_cache_overwrites(self):
        db.set_cached_response("test:apple", [{"v": 1}])
        db.set_cached_response("test:apple", [{"v": 2}])
        cached = db.get_cached_response("test:apple")
        assert cached[0]["v"] == 2
