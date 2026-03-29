import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(r"d:\ATP(clonned)\Smart-trip-planner")

from app.services.packing_service import generate_ai_packing_list

# Mock Trip and Flask App for testing service in isolation
class MockTrip:
    def __init__(self):
        self.destinations_raw = "Paris, France"
        self.number_of_days = 5
        self.start_date = "2026-06-01"
        self.itineraries = [MagicMock(weather_summary="Sunny and warm, 25°C")]

mock_app = MagicMock()
mock_app.config = {
    "GOOGLE_GEMINI_AI_API_KEY": os.environ.get("GOOGLE_GEMINI_AI_API_KEY", "dummy_key"),
    "GEMINI_MODEL": "gemini-2.0-flash" 
}

# We need a dummy context if we want to run generate_ai_packing_list 
# because it uses current_app

def test():
    from flask import Flask
    app = Flask(__name__)
    app.config.update(mock_app.config)
    
    with app.app_context():
        print("Testing with real API key check...")
        if not app.config["GOOGLE_GEMINI_AI_API_KEY"] or app.config["GOOGLE_GEMINI_AI_API_KEY"] == "dummy_key":
            print("No real API key found in environment. Mocking Gemini call.")
            # Mock the internal call if no key
            import app.services.packing_service
            app.services.packing_service.gemini_generate_json = MagicMock(return_value=[
                {"category": "Essentials", "items": ["Passport", "Tickets"]},
                {"category": "Clothing", "items": ["T-shirts", "Jeans"]}
            ])
        
        trip = MockTrip()
        items = generate_ai_packing_list(trip)
        print(f"Generated {len(items)} items.")
        for it in items:
            print(f"[{it['category']}] {it['item']} (checked: {it['checked']})")

if __name__ == "__main__":
    test()
