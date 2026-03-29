import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(r"d:\ATP(clonned)\Smart-trip-planner")

from app.services.whatsapp_service import send_trip_whatsapp_notifications

# Mock Trip, Traveler and Flask App
class MockTraveler:
    def __init__(self):
        self.phone = "+1234567890"
        self.whatsapp_opt_in = True

class MockTrip:
    def __init__(self):
        self.id = 1
        self.title = "Verification Trip"
        self.destinations_raw = "Testing Land"
        self.start_date = "2026-08-01"
        self.number_of_days = 3
        self.number_of_people = 1
        self.status = "confirmed"
        self.total_group_cost = 1000.0
        self.traveler = MockTraveler()
        self.traveler_id = 1
        self.client = None
        self.destinations = []
        self.itineraries = []
        self.bookings = []

def test():
    from flask import Flask
    app = Flask(__name__)
    app.config.update({
        "TWILIO_ACCOUNT_SID": "AC_test",
        "TWILIO_AUTH_TOKEN": "token_test",
        "TWILIO_WHATSAPP_FROM": "+14155238886",
        "APP_BASE_URL": "http://localhost:5000"
    })
    
    with app.app_context():
        print("Testing WhatsApp Notification Service...")
        
        # Mock the external API call
        import app.services.whatsapp_service
        app.services.whatsapp_service.send_whatsapp_message = MagicMock(return_value=(True, "SM_mock_sid"))
        app.services.whatsapp_service.db = MagicMock()
        
        trip = MockTrip()
        sent, total = send_trip_whatsapp_notifications(trip, "Manual Verification Test")
        
        print(f"Sent: {sent}, Total Targets: {total}")
        if sent == 1:
            print("Verification Successful: Message triggered for traveler.")
        else:
            print("Verification Failed.")

if __name__ == "__main__":
    test()
