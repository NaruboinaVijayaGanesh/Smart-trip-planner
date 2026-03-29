import json
from flask import current_app
from app.models import Trip
from app.services.gemini_service import gemini_generate_json

def generate_local_food_guide(trip: Trip) -> list[dict]:
    """Generates a curated list of regional dishes for the trip destination."""
    api_key = current_app.config.get("GOOGLE_GEMINI_AI_API_KEY")
    if not api_key:
        return []

    model = current_app.config.get("GEMINI_MODEL", "gemini-2.0-flash")
    
    destinations = trip.destinations_raw
    state_country = trip.state_country

    prompt = (
        f"You are a culinary travel expert for 'AI AIR TRIP PLANNER'.\n"
        f"Research and suggest the top 6 must-try regional dishes or food experiences for a trip to {destinations} ({state_country}).\n\n"
        "Return the guide as a JSON array of objects.\n"
        "Each object should have:\n"
        "- 'dish_name': String (Name of the dish)\n"
        "- 'description': String (Brief, appetizing description)\n"
        "- 'type': String (e.g., 'Street Food', 'Main Course', 'Dessert', 'Drink')\n"
        "- 'flavor_profile': String (e.g., 'Spicy & Savory', 'Sweet & Creamy', 'Rich & Herbaceous')\n"
        "- 'why_try': String (One sentence on why it's iconic for this region)\n\n"
        "Be specific to the culture of the region mentioned."
    )

    try:
        raw_guide = gemini_generate_json(
            prompt=prompt,
            api_key=api_key,
            model=model,
            temperature=0.5
        )
        
        if not isinstance(raw_guide, list):
            return []
            
        return raw_guide
    except Exception as e:
        current_app.logger.error(f"Failed to generate food guide: {e}")
        return []
