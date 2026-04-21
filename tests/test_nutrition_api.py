"""
Tests for nutrition_api.py — fallback database, normalization, and search.
"""
import sys, os, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database as db

@pytest.fixture(autouse=True)
def use_temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()

from nutrition_api import search_food, FALLBACK_FOODS, _norm

class TestFallbackFoods:
    def test_has_common_foods(self):
        for f in ["banana","apple","rice","egg","pizza","burger","milk","bread"]:
            assert f in FALLBACK_FOODS

    def test_has_indian_foods(self):
        for f in ["paneer","dal","roti","biryani","dosa","idli","samosa"]:
            assert f in FALLBACK_FOODS

    def test_nutrition_values_valid(self):
        for name, d in FALLBACK_FOODS.items():
            for k in ["calories","protein","fat","carbs","sugar","fiber"]:
                assert k in d and d[k] >= 0, f"{name} bad {k}"

class TestNormalization:
    def test_rounds_values(self):
        r = _norm({"name":"T","calories":100.567,"protein":5.1234}, "x")
        assert r["calories"] == 100.6
        assert r["protein"] == 5.1

    def test_missing_fields_default(self):
        r = _norm({}, "x")
        assert r["name"] == "Unknown"
        assert r["calories"] == 0.0

class TestSearchFood:
    def test_known_food(self):
        r = search_food("banana")
        assert len(r) >= 1 and r[0]["calories"] == 89

    def test_case_insensitive(self):
        r = search_food("BANANA")
        assert len(r) >= 1

    def test_unknown_food(self):
        r = search_food("xyznonexistent123")
        assert r[0]["source"] == "Not Found"

    def test_result_structure(self):
        r = search_food("apple")
        for k in ["name","calories","protein","fat","carbs","sugar","fiber","source"]:
            assert k in r[0]

    def test_limits_results(self):
        assert len(search_food("rice")) <= 8
