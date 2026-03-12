from __future__ import annotations

from datetime import datetime

from app.extensions import db
from app.models import ItineraryEditRequest, Trip
from app.services.trip_service import recalculate_trip_costs_from_current_itinerary


def pending_requests_for_trip(trip_id: int) -> list[ItineraryEditRequest]:
    return (
        ItineraryEditRequest.query.filter_by(trip_id=trip_id, status="pending")
        .order_by(ItineraryEditRequest.created_at.asc())
        .all()
    )


def pending_request_map(trip_id: int) -> dict[int, ItineraryEditRequest]:
    result = {}
    for item in pending_requests_for_trip(trip_id):
        result[item.itinerary_id] = item
    return result


def approve_request(request_row: ItineraryEditRequest, reviewer_id: int) -> None:
    itinerary = request_row.itinerary
    itinerary.title = request_row.proposed_title
    itinerary.description = request_row.proposed_description
    itinerary.ticket_price = float(request_row.proposed_ticket_price or 0)
    itinerary.map_link = request_row.proposed_map_link

    request_row.status = "approved"
    request_row.reviewer_id = reviewer_id
    request_row.reviewed_at = datetime.utcnow()

    trip: Trip = request_row.trip
    recalculate_trip_costs_from_current_itinerary(trip)
    if not pending_requests_for_trip(trip.id):
        trip.status = "confirmed"
    db.session.commit()


def reject_request(request_row: ItineraryEditRequest, reviewer_id: int) -> None:
    request_row.status = "rejected"
    request_row.reviewer_id = reviewer_id
    request_row.reviewed_at = datetime.utcnow()
    trip: Trip = request_row.trip
    if not pending_requests_for_trip(trip.id):
        trip.status = "confirmed"
    db.session.commit()


def approve_all_pending_requests(trip: Trip, reviewer_id: int) -> int:
    pending = pending_requests_for_trip(trip.id)
    if not pending:
        return 0
    for request_row in pending:
        itinerary = request_row.itinerary
        itinerary.title = request_row.proposed_title
        itinerary.description = request_row.proposed_description
        itinerary.ticket_price = float(request_row.proposed_ticket_price or 0)
        itinerary.map_link = request_row.proposed_map_link
        request_row.status = "approved"
        request_row.reviewer_id = reviewer_id
        request_row.reviewed_at = datetime.utcnow()

    recalculate_trip_costs_from_current_itinerary(trip)
    trip.status = "confirmed"
    db.session.commit()
    return len(pending)
