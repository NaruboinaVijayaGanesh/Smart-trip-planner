import os
from datetime import datetime, timedelta
from fpdf import FPDF
from icalendar import Calendar, Event
import pytz

class TripPDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, 'AI AIR TRIP PLANNER - ITINERARY', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_trip_pdf(trip, itinerary_by_day):
    """Generates a PDF document for the trip itinerary."""
    pdf = TripPDF()
    pdf.add_page()
    pdf.set_font('helvetica', '', 12)

    # Trip Info
    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(0, 10, f"Trip: {trip.title}", 0, 1)
    pdf.set_font('helvetica', '', 12)
    pdf.cell(0, 8, f"Destination(s): {trip.destinations_raw}", 0, 1)
    pdf.cell(0, 8, f"Duration: {trip.number_of_days} Days", 0, 1)
    pdf.cell(0, 8, f"Start Date: {trip.start_date.strftime('%B %d, %Y')}", 0, 1)
    pdf.cell(0, 8, f"Travelers: {trip.number_of_people}", 0, 1)
    pdf.ln(10)

    # Itinerary
    pdf.set_font('helvetica', 'B', 13)
    pdf.cell(0, 10, "Day-wise Plan", 0, 1)
    pdf.ln(2)

    for day_num in sorted(itinerary_by_day.keys()):
        pdf.set_font('helvetica', 'B', 12)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 10, f" DAY {day_num}", 0, 1, 'L', True)
        pdf.ln(2)
        
        pdf.set_font('helvetica', '', 11)
        for item in itinerary_by_day[day_num]:
            pdf.set_font('helvetica', 'B', 11)
            pdf.cell(0, 7, f"{item.time_slot}: {item.title}", 0, 1)
            pdf.set_font('helvetica', '', 10)
            pdf.multi_cell(0, 6, item.description)
            pdf.ln(2)
        pdf.ln(5)

    # Costs
    pdf.set_font('helvetica', 'B', 13)
    pdf.cell(0, 10, "Estimated Budget Summary (Total Group)", 0, 1)
    pdf.set_font('helvetica', '', 11)
    pdf.cell(40, 8, f"Transport:", 0, 0)
    pdf.cell(0, 8, f"${trip.transport_cost}", 0, 1)
    pdf.cell(40, 8, f"Hotel:", 0, 0)
    pdf.cell(0, 8, f"${trip.hotel_cost}", 0, 1)
    pdf.cell(40, 8, f"Food:", 0, 0)
    pdf.cell(0, 8, f"${trip.food_cost}", 0, 1)
    pdf.cell(40, 8, f"Activity Fees:", 0, 0)
    pdf.cell(0, 8, f"${trip.activity_cost}", 0, 1)
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(40, 10, f"TOTAL ESTIMATE:", 0, 0)
    pdf.cell(0, 10, f"${trip.total_group_cost}", 0, 1)

    return pdf.output()

def generate_trip_ics(trip):
    """Generates an iCalendar (.ics) file for the trip itinerary."""
    cal = Calendar()
    cal.add('prodid', '-//AI Air Trip Planner//EN')
    cal.add('version', '2.0')

    # Mapping time slots to approximate hours
    slot_hours = {
        "Early Morning": 7,
        "Morning": 10,
        "Afternoon": 13,
        "Evening": 17,
        "Night": 20,
        "Late Night": 23
    }

    for item in trip.itineraries:
        event = Event()
        event.add('summary', item.title)
        event.add('description', item.description)
        
        # Calculate event date
        event_date = trip.start_date + timedelta(days=max(0, item.day_number - 1))
        hour = slot_hours.get(item.time_slot, 9)
        
        start_time = datetime.combine(event_date, datetime.min.time().replace(hour=hour))
        # Set a 2-hour duration for each slot
        end_time = start_time + timedelta(hours=2)
        
        # Use UTC for simplicity or assume local time
        event.add('dtstart', start_time.replace(tzinfo=pytz.UTC))
        event.add('dtend', end_time.replace(tzinfo=pytz.UTC))
        event.add('dtstamp', datetime.now(pytz.UTC))
        
        cal.add_component(event)

    return cal.to_ical()
