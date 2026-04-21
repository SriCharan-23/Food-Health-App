"""
NutriAI - Flask Application
Main server with API routes for nutrition analysis, meal logging, and insights.
"""

from flask import Flask, render_template, request, jsonify
from database import (
    init_db, log_meal, get_meal_history, get_daily_totals,
    get_user, update_user_goal, sanitize_text
)
from nutrition_api import search_food
from recommender import (
    get_meal_insights, get_alternatives, get_habit_tip,
    compute_health_score, detect_patterns
)
import os

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False


# ── Pages ────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── API Routes ───────────────────────────────────────────────────────

@app.route("/api/search", methods=["GET"])
def api_search():
    query = request.args.get("q", "").strip()

    if not query or len(query) < 2:
        return jsonify({"error": "Query must be at least 2 characters"}), 400

    query = sanitize_text(query, 200)
    results = search_food(query)

    return jsonify({"results": results, "query": query})


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    food_name = sanitize_text(data.get("food_name", ""), 300)
    meal_type = data.get("meal_type", "snack")
    mood = sanitize_text(data.get("mood", ""), 50)
    hunger = sanitize_text(data.get("hunger", ""), 50)
    goal = sanitize_text(data.get("goal", "maintenance"), 50)

    if not food_name:
        return jsonify({"error": "Food name is required"}), 400

    results = search_food(food_name)

    if not results:
        return jsonify({"error": "Could not find nutrition data"}), 404

    nutrition = results[0]

    insights = get_meal_insights(nutrition, meal_type, mood, hunger, goal)
    alternatives = get_alternatives(food_name)
    habit = get_habit_tip(goal)
    score = compute_health_score(nutrition, goal)

    if score >= 80:
        badge = {"label": "Excellent", "class": "excellent"}
    elif score >= 60:
        badge = {"label": "Good", "class": "good"}
    elif score >= 40:
        badge = {"label": "Fair", "class": "fair"}
    else:
        badge = {"label": "Poor", "class": "poor"}

    return jsonify({
        "nutrition": nutrition,
        "score": score,
        "badge": badge,
        "insights": insights,
        "alternatives": alternatives,
        "habit": habit,
        "meal_type": meal_type,
    })


@app.route("/api/log", methods=["POST"])
def api_log():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    food_name = sanitize_text(data.get("food_name", ""), 300)
    meal_type = data.get("meal_type", "snack")
    nutrition = data.get("nutrition", {})
    mood = sanitize_text(data.get("mood", ""), 50)
    hunger = sanitize_text(data.get("hunger", ""), 50)

    if not food_name:
        return jsonify({"error": "Food name is required"}), 400

    meal_id = log_meal(1, food_name, meal_type, nutrition, mood, hunger)

    return jsonify({
        "success": True,
        "meal_id": meal_id,
        "message": f"Logged: {food_name}"
    })


@app.route("/api/history", methods=["GET"])
def api_history():
    days = request.args.get("days", 7, type=int)
    days = max(1, min(days, 90))

    meals = get_meal_history(1, days)

    return jsonify({"meals": meals, "count": len(meals)})


@app.route("/api/insights", methods=["GET"])
def api_insights():
    user = get_user(1)
    goal = user["health_goal"] if user else "maintenance"

    daily = get_daily_totals(1, 7)
    patterns = detect_patterns(daily, goal)
    tip = get_habit_tip(goal)

    return jsonify({
        "patterns": patterns,
        "daily_totals": daily,
        "tip": tip,
        "goal": goal,
    })


@app.route("/api/user", methods=["GET"])
def api_get_user():
    user = get_user(1)
    return jsonify(user or {
        "id": 1,
        "name": "User",
        "health_goal": "maintenance"
    })


@app.route("/api/user/goal", methods=["POST"])
def api_update_goal():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    goal = sanitize_text(data.get("goal", "maintenance"), 50)
    target = data.get("calorie_target", 2000)

    update_user_goal(1, goal, target)

    return jsonify({"success": True, "goal": goal})


# ── Error Handlers ───────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


# ── CLOUD RUN ENTRY POINT (IMPORTANT) ────────────────────────────────

if __name__ == "__main__":
    init_db()

    port = int(os.environ.get("PORT", 8080))

    app.run(host="0.0.0.0", port=port, debug=False)
