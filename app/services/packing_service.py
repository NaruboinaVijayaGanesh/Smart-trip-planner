import json
from flask import current_app
from app.models import Trip
from app.services.gemini_service import gemini_generate_json

def generate_ai_packing_list(trip: Trip) -> list[dict]:
    """Generates a personalized packing list using Gemini AI."""
    api_key = current_app.config.get("GOOGLE_GEMINI_AI_API_KEY")
    if not api_key:
        return []

    model = current_app.config.get("GEMINI_MODEL", "gemini-3-flash-preview")
    
    # Construct context from trip
    destinations = trip.destinations_raw
    duration = trip.number_of_days
    start_date = trip.start_date
    start_date = trip.start_date
    activities = [it.title for it in trip.itineraries[:12] if it.title] # Sample first 12 non-null activity titles
    activity_str = ", ".join(map(str, activities)) if activities else "General sightseeing"
    weather = trip.itineraries[0].weather_summary if trip.itineraries else "Unknown"

    prompt = (
        f"You are a travel assistant for 'AI AIR TRIP PLANNER'.\n"
        f"Generate a personalized travel packing checklist for a trip to {destinations}.\n"
        f"Trip Context:\n"
        f"- Duration: {duration} days\n"
        f"- Start Date: {start_date}\n"
        f"- Weather: {weather}\n"
        f"- Activities: {activity_str}\n\n"
        "Return the checklist as a JSON array of category objects.\n"
        "Each category object should have:\n"
        "- 'category': String (e.g., 'Essentials', 'Clothing', 'Electronics', 'Personal Care')\n"
        "- 'items': Array of strings (each string is a specific item to pack)\n\n"
        "Be specific and helpful. For example, if it's hot, suggest sunscreen. If they are trekking, suggest boots."
    )

    try:
        raw_list = gemini_generate_json(
            prompt=prompt,
            api_key=api_key,
            model=model,
            temperature=0.4
        )
        
        if not isinstance(raw_list, list):
            return []

        # Transform the categorized list into a flat list of items with the category as a property
        # AND add a 'checked' state.
        final_list = []
        for cat_obj in raw_list:
            category = cat_obj.get("category", "General")
            items = cat_obj.get("items", [])
            for item_name in items:
                final_list.append({
                    "id": f"{category.lower().replace(' ', '_')}_{len(final_list)}",
                    "category": category,
                    "item": item_name,
                    "checked": False
                })
        
        return final_list
    except Exception as e:
        current_app.logger.error(f"Failed to generate packing list: {e}")
        return []
