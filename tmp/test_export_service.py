import sys
import os
from unittest.mock import MagicMock
from datetime import date

# Add project root to path
sys.path.append(r"d:\ATP(clonned)\Smart-trip-planner")

from app.services.export_service import generate_trip_pdf, generate_trip_ics

# Mock Trip and Itinerary items
class MockItinerary:
    def __init__(self, day, slot, title, desc):
        self.day_number = day
        self.time_slot = slot
        self.title = title
        self.description = desc

class MockTrip:
    def __init__(self):
        self.id = 123
        self.title = "Test Vacation"
        self.destinations_raw = "Maldives"
        self.number_of_days = 2
        self.start_date = date(2026, 7, 1)
        self.number_of_people = 2
        self.transport_cost = 500.0
        self.hotel_cost = 1200.0
        self.food_cost = 400.0
        self.activity_cost = 300.0
        self.total_group_cost = 2400.0
        self.itineraries = [
            MockItinerary(1, "Morning", "Scuba Diving", "Explore the coral reefs."),
            MockItinerary(1, "Evening", "Beach Dinner", "Romantic dinner by the sea."),
            MockItinerary(2, "Afternoon", "Island Hopping", "Visit nearby local islands.")
        ]

def test():
    print("Testing Export Service...")
    trip = MockTrip()
    itinerary_by_day = {1: trip.itineraries[:2], 2: [trip.itineraries[2]]}
    
    # Test PDF
    print("Generating PDF...")
    try:
        pdf_bytes = generate_trip_pdf(trip, itinerary_by_day)
        with open(r"d:\ATP(clonned)\Smart-trip-planner\tmp\test_itinerary.pdf", "wb") as f:
            f.write(pdf_bytes)
        print("PDF generated successfully at tmp/test_itinerary.pdf")
    except Exception as e:
        print(f"PDF generation failed: {e}")

    # Test ICS
    print("Generating ICS...")
    try:
        ics_bytes = generate_trip_ics(trip)
        with open(r"d:\ATP(clonned)\Smart-trip-planner\tmp\test_itinerary.ics", "wb") as f:
            f.write(ics_bytes)
        print("ICS generated successfully at tmp/test_itinerary.ics")
    except Exception as e:
        print(f"ICS generation failed: {e}")

if __name__ == "__main__":
    test()
