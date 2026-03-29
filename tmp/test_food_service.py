import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(r"d:\ATP(clonned)\Smart-trip-planner")

from app.services.food_recommendation_service import generate_local_food_guide

# Mock Trip and Flask App for testing service in isolation
class MockTrip:
    def __init__(self):
        self.destinations_raw = "Jaipur, India"
        self.state_country = "Rajasthan, India"

def test():
    from flask import Flask
    app = Flask(__name__)
    app.config.update({
        "GOOGLE_GEMINI_AI_API_KEY": os.environ.get("GOOGLE_GEMINI_AI_API_KEY", "dummy_key"),
        "GEMINI_MODEL": "gemini-2.0-flash" 
    })
    
    with app.app_context():
        print("Testing Food Guide Service...")
        if not app.config["GOOGLE_GEMINI_AI_API_KEY"] or app.config["GOOGLE_GEMINI_AI_API_KEY"] == "dummy_key":
            print("No real API key found. Mocking Gemini call.")
            import app.services.food_recommendation_service
            app.services.food_recommendation_service.gemini_generate_json = MagicMock(return_value=[
                {
                    "dish_name": "Dal Baati Churma",
                    "description": "Lentils served with hard wheat rolls and sweet crumbled wheat.",
                    "type": "Main Course",
                    "flavor_profile": "Savory & Sweet",
                    "why_try": "It's the signature dish of Rajasthan."
                },
                {
                    "dish_name": "Laal Maas",
                    "description": "A spicy mutton curry prepared with curd and red chillies.",
                    "type": "Main Course",
                    "flavor_profile": "Extremely Spicy",
                    "why_try": "A legendary warrior dish from the Rajput era."
                }
            ])
        
        trip = MockTrip()
        guide = generate_local_food_guide(trip)
        print(f"Generated {len(guide)} dishes.")
        for dish in guide:
            print(f"- {dish['dish_name']} ({dish['type']}): {dish['flavor_profile']}")
            print(f"  {dish['description']}")

if __name__ == "__main__":
    test()
