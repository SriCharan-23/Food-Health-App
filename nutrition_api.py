"""
NutriAI - Nutrition API Clients
Open Food Facts + USDA FoodData Central with caching & fallback.
"""
import requests
import os
from database import get_cached_response, set_cached_response

USDA_API_KEY = os.environ.get("USDA_API_KEY", "")
OFF_BASE = "https://world.openfoodfacts.org/cgi/search.pl"
USDA_BASE = "https://api.nal.usda.gov/fdc/v1/foods/search"

FALLBACK_FOODS = {
    "banana": {"name":"Banana","calories":89,"protein":1.1,"fat":0.3,"carbs":23,"sugar":12,"fiber":2.6,"serving_size":"1 medium (118g)"},
    "apple": {"name":"Apple","calories":52,"protein":0.3,"fat":0.2,"carbs":14,"sugar":10,"fiber":2.4,"serving_size":"1 medium (182g)"},
    "rice": {"name":"White Rice (cooked)","calories":130,"protein":2.7,"fat":0.3,"carbs":28,"sugar":0.1,"fiber":0.4,"serving_size":"1 cup (158g)"},
    "chicken breast": {"name":"Chicken Breast (grilled)","calories":165,"protein":31,"fat":3.6,"carbs":0,"sugar":0,"fiber":0,"serving_size":"100g"},
    "egg": {"name":"Egg (boiled)","calories":155,"protein":13,"fat":11,"carbs":1.1,"sugar":1.1,"fiber":0,"serving_size":"1 large (50g)"},
    "pizza": {"name":"Pizza (cheese)","calories":266,"protein":11,"fat":10,"carbs":33,"sugar":3.6,"fiber":2.3,"serving_size":"1 slice (107g)"},
    "burger": {"name":"Hamburger","calories":295,"protein":17,"fat":14,"carbs":24,"sugar":5,"fiber":1.3,"serving_size":"1 burger"},
    "salad": {"name":"Garden Salad","calories":20,"protein":1.5,"fat":0.2,"carbs":3.5,"sugar":1.5,"fiber":2,"serving_size":"1 bowl (100g)"},
    "milk": {"name":"Whole Milk","calories":61,"protein":3.2,"fat":3.3,"carbs":4.8,"sugar":5,"fiber":0,"serving_size":"1 cup (244ml)"},
    "bread": {"name":"White Bread","calories":265,"protein":9,"fat":3.2,"carbs":49,"sugar":5,"fiber":2.7,"serving_size":"2 slices"},
    "pasta": {"name":"Pasta (cooked)","calories":131,"protein":5,"fat":1.1,"carbs":25,"sugar":0.6,"fiber":1.8,"serving_size":"1 cup"},
    "oatmeal": {"name":"Oatmeal","calories":68,"protein":2.4,"fat":1.4,"carbs":12,"sugar":0.5,"fiber":1.7,"serving_size":"1 cup cooked"},
    "salmon": {"name":"Salmon (baked)","calories":208,"protein":20,"fat":13,"carbs":0,"sugar":0,"fiber":0,"serving_size":"100g"},
    "yogurt": {"name":"Greek Yogurt","calories":59,"protein":10,"fat":0.7,"carbs":3.6,"sugar":3.2,"fiber":0,"serving_size":"1 cup"},
    "chips": {"name":"Potato Chips","calories":536,"protein":7,"fat":35,"carbs":53,"sugar":0.3,"fiber":4.4,"serving_size":"1 bag (28g)"},
    "soda": {"name":"Cola Soda","calories":140,"protein":0,"fat":0,"carbs":39,"sugar":39,"fiber":0,"serving_size":"1 can (355ml)"},
    "chocolate": {"name":"Milk Chocolate","calories":535,"protein":8,"fat":30,"carbs":59,"sugar":52,"fiber":3.4,"serving_size":"1 bar (44g)"},
    "avocado": {"name":"Avocado","calories":160,"protein":2,"fat":15,"carbs":9,"sugar":0.7,"fiber":7,"serving_size":"1/2 avocado"},
    "lentils": {"name":"Lentils (cooked)","calories":116,"protein":9,"fat":0.4,"carbs":20,"sugar":1.8,"fiber":7.9,"serving_size":"1 cup"},
    "sweet potato": {"name":"Sweet Potato","calories":90,"protein":2,"fat":0.1,"carbs":21,"sugar":6.5,"fiber":3.3,"serving_size":"1 medium"},
    "broccoli": {"name":"Broccoli","calories":35,"protein":2.4,"fat":0.4,"carbs":7,"sugar":1.4,"fiber":3.3,"serving_size":"1 cup"},
    "almonds": {"name":"Almonds","calories":579,"protein":21,"fat":50,"carbs":22,"sugar":4.4,"fiber":12,"serving_size":"1/4 cup"},
    "coffee": {"name":"Black Coffee","calories":2,"protein":0.3,"fat":0,"carbs":0,"sugar":0,"fiber":0,"serving_size":"1 cup"},
    "ice cream": {"name":"Vanilla Ice Cream","calories":207,"protein":3.5,"fat":11,"carbs":24,"sugar":21,"fiber":0.7,"serving_size":"1/2 cup"},
    "french fries": {"name":"French Fries","calories":312,"protein":3.4,"fat":15,"carbs":41,"sugar":0.3,"fiber":3.8,"serving_size":"1 serving"},
    "paneer": {"name":"Paneer","calories":265,"protein":18,"fat":20,"carbs":3.6,"sugar":2,"fiber":0,"serving_size":"100g"},
    "dal": {"name":"Dal (Lentil Curry)","calories":120,"protein":8,"fat":3,"carbs":16,"sugar":2,"fiber":5,"serving_size":"1 bowl"},
    "roti": {"name":"Whole Wheat Roti","calories":120,"protein":3.5,"fat":3.7,"carbs":18,"sugar":0.4,"fiber":2,"serving_size":"1 roti"},
    "biryani": {"name":"Chicken Biryani","calories":250,"protein":12,"fat":10,"carbs":30,"sugar":2,"fiber":1.5,"serving_size":"1 cup"},
    "dosa": {"name":"Plain Dosa","calories":120,"protein":3,"fat":3,"carbs":20,"sugar":1,"fiber":0.8,"serving_size":"1 dosa"},
    "idli": {"name":"Idli","calories":39,"protein":2,"fat":0.2,"carbs":8,"sugar":0.5,"fiber":0.5,"serving_size":"1 idli"},
    "samosa": {"name":"Samosa","calories":262,"protein":4.5,"fat":17,"carbs":24,"sugar":2,"fiber":2,"serving_size":"1 samosa"},
    "smoothie": {"name":"Fruit Smoothie","calories":135,"protein":3,"fat":0.5,"carbs":32,"sugar":28,"fiber":2.5,"serving_size":"1 glass"},
    "orange": {"name":"Orange","calories":47,"protein":0.9,"fat":0.1,"carbs":12,"sugar":9.4,"fiber":2.4,"serving_size":"1 medium"},
    "tofu": {"name":"Tofu (firm)","calories":76,"protein":8,"fat":4.8,"carbs":1.9,"sugar":0.5,"fiber":0.3,"serving_size":"100g"},
}


def _norm(raw, source="unknown"):
    return {
        "name": str(raw.get("name","Unknown")),
        "calories": round(float(raw.get("calories",0)),1),
        "protein": round(float(raw.get("protein",0)),1),
        "fat": round(float(raw.get("fat",0)),1),
        "carbs": round(float(raw.get("carbs",0)),1),
        "sugar": round(float(raw.get("sugar",0)),1),
        "fiber": round(float(raw.get("fiber",0)),1),
        "serving_size": str(raw.get("serving_size","100g")),
        "source": source,
    }


def search_open_food_facts(query, page_size=5):
    cache_key = f"off:{query.lower().strip()}"
    cached = get_cached_response(cache_key)
    if cached:
        return cached
    try:
        r = requests.get(OFF_BASE, params={
            "search_terms": query, "search_simple": 1,
            "action": "process", "json": 1, "page_size": page_size,
            "fields": "product_name,nutriments,serving_size",
        }, timeout=8)
        r.raise_for_status()
        results = []
        for p in r.json().get("products", []):
            n = p.get("nutriments", {})
            nm = p.get("product_name", "")
            if not nm:
                continue
            results.append(_norm({
                "name": nm,
                "calories": n.get("energy-kcal_100g", n.get("energy-kcal", 0)),
                "protein": n.get("proteins_100g", 0),
                "fat": n.get("fat_100g", 0),
                "carbs": n.get("carbohydrates_100g", 0),
                "sugar": n.get("sugars_100g", 0),
                "fiber": n.get("fiber_100g", 0),
                "serving_size": p.get("serving_size", "100g"),
            }, source="Open Food Facts"))
        if results:
            set_cached_response(cache_key, results)
        return results
    except Exception as e:
        print(f"[OFF Error] {e}")
        return []


def search_usda(query, page_size=5):
    if not USDA_API_KEY:
        return []
    cache_key = f"usda:{query.lower().strip()}"
    cached = get_cached_response(cache_key)
    if cached:
        return cached
    try:
        r = requests.get(USDA_BASE, params={
            "api_key": USDA_API_KEY, "query": query,
            "pageSize": page_size, "dataType": "Foundation,SR Legacy",
        }, timeout=8)
        r.raise_for_status()
        results = []
        for food in r.json().get("foods", []):
            nuts = {n["nutrientName"]: n.get("value",0) for n in food.get("foodNutrients",[])}
            results.append(_norm({
                "name": food.get("description","Unknown"),
                "calories": nuts.get("Energy",0),
                "protein": nuts.get("Protein",0),
                "fat": nuts.get("Total lipid (fat)",0),
                "carbs": nuts.get("Carbohydrate, by difference",0),
                "sugar": nuts.get("Sugars, total including NLEA", nuts.get("Total Sugars",0)),
                "fiber": nuts.get("Fiber, total dietary",0),
            }, source="USDA"))
        if results:
            set_cached_response(cache_key, results)
        return results
    except Exception as e:
        print(f"[USDA Error] {e}")
        return []


def search_food(query):
    q = query.lower().strip()
    fallback = None
    for key, val in FALLBACK_FOODS.items():
        if key in q or q in key:
            fallback = _norm(val, source="NutriAI Database")
            break

    off = search_open_food_facts(query)
    usda = search_usda(query)
    combined = off + usda
    if fallback:
        combined.insert(0, fallback)
    if not combined and fallback:
        combined = [fallback]
    if not combined:
        return [{"name": query.title(), "calories":0,"protein":0,"fat":0,
                 "carbs":0,"sugar":0,"fiber":0,"serving_size":"unknown","source":"Not Found"}]
    return combined[:8]
