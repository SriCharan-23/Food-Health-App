"""
Tests for Flask routes in app.py
"""
import sys, os, json, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database as db

@pytest.fixture(autouse=True)
def use_temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()

from app import app as flask_app

@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c

class TestHomePage:
    def test_index_returns_200(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert b"NutriAI" in r.data

class TestSearchAPI:
    def test_search_valid(self, client):
        r = client.get("/api/search?q=banana")
        assert r.status_code == 200
        data = r.get_json()
        assert "results" in data
        assert len(data["results"]) >= 1

    def test_search_too_short(self, client):
        r = client.get("/api/search?q=a")
        assert r.status_code == 400

    def test_search_empty(self, client):
        r = client.get("/api/search?q=")
        assert r.status_code == 400

class TestAnalyzeAPI:
    def test_analyze_valid(self, client):
        r = client.post("/api/analyze",
            data=json.dumps({"food_name":"banana","meal_type":"breakfast","goal":"maintenance"}),
            content_type="application/json")
        assert r.status_code == 200
        data = r.get_json()
        assert "nutrition" in data
        assert "score" in data
        assert "insights" in data
        assert "alternatives" in data
        assert "habit" in data
        assert 0 <= data["score"] <= 100

    def test_analyze_empty_food(self, client):
        r = client.post("/api/analyze",
            data=json.dumps({"food_name":""}),
            content_type="application/json")
        assert r.status_code == 400

    def test_analyze_no_body(self, client):
        r = client.post("/api/analyze")
        assert r.status_code == 400

    def test_analyze_with_mood(self, client):
        r = client.post("/api/analyze",
            data=json.dumps({"food_name":"chocolate","meal_type":"snack","mood":"stressed","goal":"weight-loss"}),
            content_type="application/json")
        data = r.get_json()
        assert data["score"] is not None
        texts = [i["text"] for i in data["insights"]]
        assert any("stress" in t.lower() for t in texts)

class TestLogAPI:
    def test_log_meal(self, client):
        r = client.post("/api/log",
            data=json.dumps({"food_name":"Rice","meal_type":"lunch","nutrition":{"calories":130,"protein":2.7}}),
            content_type="application/json")
        assert r.status_code == 200
        assert r.get_json()["success"] is True

    def test_log_empty_food(self, client):
        r = client.post("/api/log",
            data=json.dumps({"food_name":"","meal_type":"lunch","nutrition":{}}),
            content_type="application/json")
        assert r.status_code == 400

    def test_log_no_body(self, client):
        r = client.post("/api/log")
        assert r.status_code == 400

class TestHistoryAPI:
    def test_empty_history(self, client):
        r = client.get("/api/history")
        assert r.status_code == 200
        assert r.get_json()["count"] == 0

    def test_history_after_log(self, client):
        client.post("/api/log",
            data=json.dumps({"food_name":"Egg","meal_type":"breakfast","nutrition":{"calories":155}}),
            content_type="application/json")
        r = client.get("/api/history")
        data = r.get_json()
        assert data["count"] >= 1
        assert data["meals"][0]["food_name"] == "Egg"

    def test_history_days_param(self, client):
        r = client.get("/api/history?days=1")
        assert r.status_code == 200

class TestInsightsAPI:
    def test_insights_empty(self, client):
        r = client.get("/api/insights")
        assert r.status_code == 200
        data = r.get_json()
        assert "patterns" in data
        assert "tip" in data

class TestUserAPI:
    def test_get_user(self, client):
        r = client.get("/api/user")
        assert r.status_code == 200
        data = r.get_json()
        assert data["health_goal"] == "maintenance"

    def test_update_goal(self, client):
        r = client.post("/api/user/goal",
            data=json.dumps({"goal":"weight-loss"}),
            content_type="application/json")
        assert r.status_code == 200
        assert r.get_json()["goal"] == "weight-loss"
        # Verify persisted
        r2 = client.get("/api/user")
        assert r2.get_json()["health_goal"] == "weight-loss"

class TestErrorHandling:
    def test_404(self, client):
        r = client.get("/nonexistent")
        assert r.status_code == 404
