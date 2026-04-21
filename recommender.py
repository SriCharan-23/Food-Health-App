"""
NutriAI - Recommendation Engine
Pattern detection, alternative suggestions, and behavioral nudges.
"""

ALTERNATIVES = {
    "pizza": [
        {"name": "Whole wheat pizza with veggies", "why": "More fiber, less refined carbs", "save": "~80 cal"},
        {"name": "Cauliflower crust pizza", "why": "Lower carbs, more nutrients", "save": "~100 cal"},
    ],
    "burger": [
        {"name": "Grilled chicken sandwich", "why": "Leaner protein, less saturated fat", "save": "~120 cal"},
        {"name": "Turkey burger with lettuce wrap", "why": "Lower fat, fewer carbs", "save": "~150 cal"},
    ],
    "soda": [
        {"name": "Sparkling water with lemon", "why": "Zero sugar, equally refreshing", "save": "~140 cal"},
        {"name": "Green tea (unsweetened)", "why": "Antioxidants, zero sugar", "save": "~140 cal"},
    ],
    "chips": [
        {"name": "Air-popped popcorn", "why": "Whole grain, much less fat", "save": "~350 cal"},
        {"name": "Roasted almonds (small portion)", "why": "Healthy fats, protein-rich", "save": "~200 cal"},
    ],
    "chocolate": [
        {"name": "Dark chocolate (70%+)", "why": "Less sugar, more antioxidants", "save": "~80 cal"},
        {"name": "Cocoa-dusted almonds", "why": "Protein + chocolate flavor", "save": "~150 cal"},
    ],
    "ice cream": [
        {"name": "Frozen Greek yogurt", "why": "More protein, less sugar", "save": "~100 cal"},
        {"name": "Banana nice cream", "why": "Natural sweetness, no added sugar", "save": "~120 cal"},
    ],
    "french fries": [
        {"name": "Baked sweet potato fries", "why": "More fiber, vitamins A & C", "save": "~100 cal"},
        {"name": "Roasted vegetables", "why": "Nutrient-dense, lower calorie", "save": "~200 cal"},
    ],
    "bread": [
        {"name": "Whole wheat bread", "why": "More fiber, B vitamins", "save": "~30 cal"},
        {"name": "Ezekiel sprouted bread", "why": "Complete protein, easier to digest", "save": "~40 cal"},
    ],
    "rice": [
        {"name": "Brown rice", "why": "3x more fiber, more minerals", "save": "~10 cal"},
        {"name": "Quinoa", "why": "Complete protein, higher fiber", "save": "~10 cal"},
    ],
    "pasta": [
        {"name": "Whole wheat pasta", "why": "More fiber and protein", "save": "~20 cal"},
        {"name": "Zucchini noodles", "why": "90% fewer calories, more vitamins", "save": "~110 cal"},
    ],
    "naan": [
        {"name": "Whole wheat roti", "why": "Less oil, more fiber", "save": "~140 cal"},
        {"name": "Multigrain roti", "why": "Better nutrient profile", "save": "~130 cal"},
    ],
    "samosa": [
        {"name": "Baked samosa", "why": "80% less oil", "save": "~100 cal"},
        {"name": "Sprout chaat", "why": "Protein-rich, no deep frying", "save": "~180 cal"},
    ],
    "biryani": [
        {"name": "Brown rice pulao with chicken", "why": "More fiber, less oil", "save": "~80 cal"},
        {"name": "Quinoa biryani", "why": "Complete protein grain", "save": "~60 cal"},
    ],
}

GOAL_TIPS = {
    "weight-loss": [
        {"icon": "🥗", "text": "Try eating a small salad before your main meal — it reduces total intake by ~12%."},
        {"icon": "💧", "text": "Drink a glass of water 30 min before meals. Often thirst is confused with hunger."},
        {"icon": "🍽️", "text": "Use a smaller plate — visual cues affect portion size more than you think."},
        {"icon": "⏰", "text": "Try to finish eating by 8 PM. Late-night eating increases fat storage."},
        {"icon": "🚶", "text": "A 10-minute walk after meals improves blood sugar and digestion."},
    ],
    "muscle-gain": [
        {"icon": "💪", "text": "Aim for 1.6–2.2g protein per kg bodyweight daily for muscle growth."},
        {"icon": "🥚", "text": "Include protein in every meal. Spread intake across 4–5 meals for better absorption."},
        {"icon": "🍌", "text": "Eat carbs + protein within 2 hours post-workout for optimal recovery."},
        {"icon": "😴", "text": "Sleep 7–9 hours — muscles grow during rest, not just in the gym."},
        {"icon": "🥜", "text": "Add calorie-dense healthy foods: nuts, avocado, olive oil to hit surplus."},
    ],
    "diabetes-control": [
        {"icon": "📊", "text": "Choose low glycemic index foods — they release sugar slowly into blood."},
        {"icon": "🥦", "text": "Pair carbs with fiber or protein to slow sugar absorption."},
        {"icon": "⏰", "text": "Eat at consistent times daily to stabilize blood sugar levels."},
        {"icon": "🚫", "text": "Avoid sugary drinks entirely — they cause rapid blood sugar spikes."},
        {"icon": "🏃", "text": "A short walk after meals can lower post-meal blood sugar by 30%."},
    ],
    "heart-health": [
        {"icon": "🐟", "text": "Eat fatty fish (salmon, mackerel) 2x/week for heart-protective omega-3s."},
        {"icon": "🧂", "text": "Keep sodium under 2300mg/day. Use herbs and spices instead of salt."},
        {"icon": "🫒", "text": "Use olive oil or avocado oil instead of butter for cooking."},
        {"icon": "🥬", "text": "Add leafy greens daily — they're rich in nitrates that lower blood pressure."},
        {"icon": "🚫", "text": "Limit processed meats — they increase heart disease risk by 42%."},
    ],
    "maintenance": [
        {"icon": "⚖️", "text": "You're doing great maintaining! Focus on variety to cover all micronutrients."},
        {"icon": "🌈", "text": "Eat the rainbow — different colored foods provide different phytonutrients."},
        {"icon": "💧", "text": "Stay hydrated — aim for 8 glasses of water daily."},
        {"icon": "🧘", "text": "Practice mindful eating: no screens, chew slowly, enjoy your food."},
        {"icon": "📅", "text": "Meal prep on weekends to maintain healthy choices during busy weekdays."},
    ],
}


def detect_patterns(daily_totals, goal):
    """Detect unhealthy patterns from daily nutrition totals."""
    patterns = []
    if not daily_totals:
        return patterns

    for day in daily_totals:
        date = day.get("date", "")
        cal = day.get("total_cal", 0) or 0
        sugar = day.get("total_sugar", 0) or 0
        protein = day.get("total_protein", 0) or 0
        fiber = day.get("total_fiber", 0) or 0
        meals = day.get("meal_count", 0) or 0

        if sugar > 50:
            patterns.append({"type": "high_sugar", "date": date,
                "msg": f"Sugar was {sugar:.0f}g on {date} (recommended: <25g)"})
        if protein < 50 and goal == "muscle-gain":
            patterns.append({"type": "low_protein", "date": date,
                "msg": f"Only {protein:.0f}g protein on {date} — aim for 100g+ for muscle gain"})
        if fiber < 10 and meals >= 2:
            patterns.append({"type": "low_fiber", "date": date,
                "msg": f"Low fiber ({fiber:.0f}g) on {date} — add vegetables, fruits, or whole grains"})
        if meals <= 1 and cal > 0:
            patterns.append({"type": "skipped_meals", "date": date,
                "msg": f"Only {meals} meal logged on {date} — skipping meals can slow metabolism"})

    # Calorie trend detection
    if len(daily_totals) >= 3:
        cals = [d.get("total_cal", 0) or 0 for d in daily_totals[-3:]]
        if all(cals[i] < cals[i+1] for i in range(len(cals)-1)):
            patterns.append({"type": "rising_calories",
                "msg": "Calorie intake is trending upward over the last 3 days — watch portions"})

    return patterns


def get_alternatives(food_name):
    """Get healthier alternatives for a food item."""
    food_lower = food_name.lower()
    for key, alts in ALTERNATIVES.items():
        if key in food_lower or food_lower in key:
            return alts
    return [
        {"name": "Add a side of vegetables", "why": "Boosts fiber and micronutrients", "save": "+nutrients"},
        {"name": "Drink water with your meal", "why": "Aids digestion and satiety", "save": "0 cal"},
    ]


def get_meal_insights(nutrition, meal_type, mood="", hunger="", goal="maintenance"):
    """Generate structured health insights for a single meal."""
    insights = []
    cal = nutrition.get("calories", 0)
    sugar = nutrition.get("sugar", 0)
    protein = nutrition.get("protein", 0)
    fat = nutrition.get("fat", 0)
    fiber = nutrition.get("fiber", 0)

    # Nutritional checks
    if sugar > 30:
        insights.append({"icon": "⚠️", "text": f"High sugar ({sugar}g) — exceeds recommended 25g/meal. Risk of energy crash."})
    elif sugar > 15:
        insights.append({"icon": "🟡", "text": f"Moderate sugar ({sugar}g). Watch total daily intake."})

    if fiber < 2:
        insights.append({"icon": "🌿", "text": f"Low fiber ({fiber}g). Add veggies or whole grains for better digestion."})

    if protein < 10 and goal == "muscle-gain":
        insights.append({"icon": "💪", "text": f"Low protein ({protein}g) for muscle gain. Add eggs, chicken, or legumes."})

    if fat > 25:
        insights.append({"icon": "🧈", "text": f"High fat ({fat}g). Prefer healthy sources: olive oil, nuts, avocado."})

    if cal > 600:
        insights.append({"icon": "🔥", "text": f"High calorie meal ({cal} kcal). Consider a lighter next meal."})

    # Contextual checks
    if meal_type == "snack" and cal > 300:
        insights.append({"icon": "🍿", "text": "Heavy snack! Keep snacks under 200 cal for better weight management."})

    if mood == "stressed":
        insights.append({"icon": "😓", "text": "Stressed eating often leads to overeating. Pause and eat mindfully."})

    if hunger == "not-hungry":
        insights.append({"icon": "🤔", "text": "Eating without hunger could be emotional. Check in with yourself."})

    if not insights:
        insights.append({"icon": "✅", "text": "Looks balanced! Great choice — keep it up!"})

    return insights


def get_habit_tip(goal="maintenance"):
    """Get a random habit tip for the user's goal."""
    import random
    tips = GOAL_TIPS.get(goal, GOAL_TIPS["maintenance"])
    return random.choice(tips)


def compute_health_score(nutrition, goal="maintenance"):
    """Compute a 0-100 health score for a meal."""
    score = 70  # baseline
    cal = nutrition.get("calories", 0)
    protein = nutrition.get("protein", 0)
    sugar = nutrition.get("sugar", 0)
    fiber = nutrition.get("fiber", 0)
    fat = nutrition.get("fat", 0)

    # Protein bonus
    if protein >= 20:
        score += 10
    elif protein >= 10:
        score += 5

    # Fiber bonus
    if fiber >= 5:
        score += 10
    elif fiber >= 2:
        score += 5

    # Sugar penalty
    if sugar > 30:
        score -= 20
    elif sugar > 15:
        score -= 10

    # Fat penalty (excess)
    if fat > 30:
        score -= 15
    elif fat > 20:
        score -= 5

    # Calorie adjustments
    if goal == "weight-loss" and cal > 500:
        score -= 10
    if goal == "muscle-gain" and protein < 15:
        score -= 10

    return max(0, min(100, score))
