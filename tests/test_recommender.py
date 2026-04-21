"""
Tests for recommender.py — insights, alternatives, scoring, and pattern detection.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recommender import (
    get_meal_insights, get_alternatives, get_habit_tip,
    compute_health_score, detect_patterns
)


# ── Health Insights Tests ──────────────────────────────────────────

class TestMealInsights:
    def test_high_sugar_warning(self):
        nutrition = {"calories": 200, "protein": 2, "fat": 5, "sugar": 35, "fiber": 1}
        insights = get_meal_insights(nutrition, "snack")
        texts = [i["text"] for i in insights]
        assert any("sugar" in t.lower() for t in texts)

    def test_low_fiber_warning(self):
        nutrition = {"calories": 300, "protein": 10, "fat": 8, "sugar": 5, "fiber": 0.5}
        insights = get_meal_insights(nutrition, "lunch")
        texts = [i["text"] for i in insights]
        assert any("fiber" in t.lower() for t in texts)

    def test_low_protein_for_muscle_gain(self):
        nutrition = {"calories": 200, "protein": 3, "fat": 5, "sugar": 10, "fiber": 3}
        insights = get_meal_insights(nutrition, "lunch", goal="muscle-gain")
        texts = [i["text"] for i in insights]
        assert any("protein" in t.lower() for t in texts)

    def test_no_protein_warning_for_maintenance(self):
        nutrition = {"calories": 200, "protein": 3, "fat": 5, "sugar": 5, "fiber": 3}
        insights = get_meal_insights(nutrition, "lunch", goal="maintenance")
        texts = [i["text"] for i in insights]
        # Should NOT flag low protein for maintenance
        assert not any("protein" in t.lower() and "low" in t.lower() for t in texts)

    def test_high_fat_warning(self):
        nutrition = {"calories": 500, "protein": 10, "fat": 30, "sugar": 5, "fiber": 3}
        insights = get_meal_insights(nutrition, "dinner")
        texts = [i["text"] for i in insights]
        assert any("fat" in t.lower() for t in texts)

    def test_high_calorie_warning(self):
        nutrition = {"calories": 800, "protein": 20, "fat": 15, "sugar": 10, "fiber": 5}
        insights = get_meal_insights(nutrition, "lunch")
        texts = [i["text"] for i in insights]
        assert any("calorie" in t.lower() for t in texts)

    def test_stressed_mood_insight(self):
        nutrition = {"calories": 200, "protein": 10, "fat": 5, "sugar": 5, "fiber": 3}
        insights = get_meal_insights(nutrition, "lunch", mood="stressed")
        texts = [i["text"] for i in insights]
        assert any("stressed" in t.lower() or "stress" in t.lower() for t in texts)

    def test_not_hungry_insight(self):
        nutrition = {"calories": 200, "protein": 10, "fat": 5, "sugar": 5, "fiber": 3}
        insights = get_meal_insights(nutrition, "lunch", hunger="not-hungry")
        texts = [i["text"] for i in insights]
        assert any("hunger" in t.lower() or "emotional" in t.lower() for t in texts)

    def test_balanced_meal_positive(self):
        nutrition = {"calories": 350, "protein": 25, "fat": 10, "sugar": 5, "fiber": 6}
        insights = get_meal_insights(nutrition, "lunch", goal="maintenance")
        texts = [i["text"] for i in insights]
        assert any("balanced" in t.lower() or "great" in t.lower() for t in texts)

    def test_heavy_snack_warning(self):
        nutrition = {"calories": 400, "protein": 5, "fat": 20, "sugar": 15, "fiber": 1}
        insights = get_meal_insights(nutrition, "snack")
        texts = [i["text"] for i in insights]
        assert any("snack" in t.lower() for t in texts)

    def test_insights_always_return_list(self):
        nutrition = {"calories": 0, "protein": 0, "fat": 0, "sugar": 0, "fiber": 0}
        insights = get_meal_insights(nutrition, "lunch")
        assert isinstance(insights, list)
        assert len(insights) >= 1

    def test_insight_structure(self):
        nutrition = {"calories": 500, "protein": 10, "fat": 20, "sugar": 30, "fiber": 1}
        insights = get_meal_insights(nutrition, "dinner")
        for item in insights:
            assert "icon" in item
            assert "text" in item
            assert isinstance(item["text"], str)


# ── Alternatives Tests ─────────────────────────────────────────────

class TestAlternatives:
    def test_known_food_alternatives(self):
        alts = get_alternatives("pizza")
        assert len(alts) >= 1
        assert "name" in alts[0]
        assert "why" in alts[0]

    def test_burger_alternatives(self):
        alts = get_alternatives("burger")
        assert len(alts) >= 1

    def test_unknown_food_gets_defaults(self):
        alts = get_alternatives("exotic_dragon_fruit_sundae")
        assert len(alts) >= 1
        # Should return generic helpful alternatives
        assert any("name" in a for a in alts)

    def test_case_insensitive_match(self):
        alts = get_alternatives("PIZZA")
        assert len(alts) >= 1

    def test_alternative_structure(self):
        alts = get_alternatives("soda")
        for alt in alts:
            assert "name" in alt
            assert "why" in alt


# ── Health Score Tests ─────────────────────────────────────────────

class TestHealthScore:
    def test_score_range(self):
        nutrition = {"calories": 300, "protein": 20, "fat": 10, "sugar": 5, "fiber": 5}
        score = compute_health_score(nutrition)
        assert 0 <= score <= 100

    def test_healthy_meal_high_score(self):
        nutrition = {"calories": 350, "protein": 25, "fat": 8, "sugar": 3, "fiber": 7}
        score = compute_health_score(nutrition)
        assert score >= 70

    def test_unhealthy_meal_low_score(self):
        nutrition = {"calories": 800, "protein": 3, "fat": 35, "sugar": 45, "fiber": 0}
        score = compute_health_score(nutrition)
        assert score <= 50

    def test_score_penalizes_high_sugar(self):
        low_sugar = {"calories": 200, "protein": 10, "fat": 5, "sugar": 5, "fiber": 3}
        high_sugar = {"calories": 200, "protein": 10, "fat": 5, "sugar": 40, "fiber": 3}
        assert compute_health_score(low_sugar) > compute_health_score(high_sugar)

    def test_score_rewards_protein(self):
        low_protein = {"calories": 200, "protein": 2, "fat": 5, "sugar": 5, "fiber": 3}
        high_protein = {"calories": 200, "protein": 25, "fat": 5, "sugar": 5, "fiber": 3}
        assert compute_health_score(high_protein) > compute_health_score(low_protein)

    def test_score_rewards_fiber(self):
        low_fiber = {"calories": 200, "protein": 10, "fat": 5, "sugar": 5, "fiber": 0}
        high_fiber = {"calories": 200, "protein": 10, "fat": 5, "sugar": 5, "fiber": 8}
        assert compute_health_score(high_fiber) > compute_health_score(low_fiber)

    def test_weight_loss_goal_penalty(self):
        nutrition = {"calories": 700, "protein": 20, "fat": 15, "sugar": 10, "fiber": 5}
        maintenance_score = compute_health_score(nutrition, "maintenance")
        weightloss_score = compute_health_score(nutrition, "weight-loss")
        assert weightloss_score < maintenance_score

    def test_muscle_gain_low_protein_penalty(self):
        nutrition = {"calories": 300, "protein": 5, "fat": 10, "sugar": 5, "fiber": 3}
        maintenance_score = compute_health_score(nutrition, "maintenance")
        muscle_score = compute_health_score(nutrition, "muscle-gain")
        assert muscle_score < maintenance_score

    def test_score_never_negative(self):
        terrible = {"calories": 2000, "protein": 0, "fat": 80, "sugar": 100, "fiber": 0}
        score = compute_health_score(terrible, "weight-loss")
        assert score >= 0

    def test_score_never_exceeds_100(self):
        perfect = {"calories": 300, "protein": 40, "fat": 5, "sugar": 0, "fiber": 15}
        score = compute_health_score(perfect)
        assert score <= 100


# ── Pattern Detection Tests ────────────────────────────────────────

class TestPatternDetection:
    def test_high_sugar_pattern(self):
        daily = [{"date": "2026-04-21", "total_cal": 1800, "total_sugar": 60,
                  "total_protein": 80, "total_fiber": 20, "meal_count": 3}]
        patterns = detect_patterns(daily, "maintenance")
        types = [p["type"] for p in patterns]
        assert "high_sugar" in types

    def test_low_protein_for_muscle_gain(self):
        daily = [{"date": "2026-04-21", "total_cal": 2000, "total_sugar": 20,
                  "total_protein": 30, "total_fiber": 25, "meal_count": 3}]
        patterns = detect_patterns(daily, "muscle-gain")
        types = [p["type"] for p in patterns]
        assert "low_protein" in types

    def test_no_low_protein_for_maintenance(self):
        daily = [{"date": "2026-04-21", "total_cal": 2000, "total_sugar": 20,
                  "total_protein": 30, "total_fiber": 25, "meal_count": 3}]
        patterns = detect_patterns(daily, "maintenance")
        types = [p["type"] for p in patterns]
        assert "low_protein" not in types

    def test_skipped_meals_pattern(self):
        daily = [{"date": "2026-04-21", "total_cal": 500, "total_sugar": 10,
                  "total_protein": 20, "total_fiber": 5, "meal_count": 1}]
        patterns = detect_patterns(daily, "maintenance")
        types = [p["type"] for p in patterns]
        assert "skipped_meals" in types

    def test_rising_calories_trend(self):
        daily = [
            {"date": "2026-04-19", "total_cal": 1500, "total_sugar": 20, "total_protein": 60, "total_fiber": 20, "meal_count": 3},
            {"date": "2026-04-20", "total_cal": 1800, "total_sugar": 20, "total_protein": 60, "total_fiber": 20, "meal_count": 3},
            {"date": "2026-04-21", "total_cal": 2200, "total_sugar": 20, "total_protein": 60, "total_fiber": 20, "meal_count": 3},
        ]
        patterns = detect_patterns(daily, "maintenance")
        types = [p["type"] for p in patterns]
        assert "rising_calories" in types

    def test_empty_data_no_crash(self):
        patterns = detect_patterns([], "maintenance")
        assert patterns == []

    def test_pattern_structure(self):
        daily = [{"date": "2026-04-21", "total_cal": 1800, "total_sugar": 60,
                  "total_protein": 80, "total_fiber": 20, "meal_count": 3}]
        patterns = detect_patterns(daily, "maintenance")
        for p in patterns:
            assert "type" in p
            assert "msg" in p


# ── Habit Tips Tests ───────────────────────────────────────────────

class TestHabitTips:
    def test_returns_tip_for_all_goals(self):
        for goal in ["weight-loss", "muscle-gain", "diabetes-control", "heart-health", "maintenance"]:
            tip = get_habit_tip(goal)
            assert "icon" in tip
            assert "text" in tip
            assert len(tip["text"]) > 10

    def test_unknown_goal_returns_maintenance(self):
        tip = get_habit_tip("unknown-goal")
        assert "icon" in tip
        assert "text" in tip
