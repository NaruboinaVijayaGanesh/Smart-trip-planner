from __future__ import annotations

from datetime import datetime

from app.extensions import db
from app.models import Trip, TripUpdateRequest
from app.services.trip_service import regenerate_trip


def pending_update_request_for_trip(trip_id: int) -> TripUpdateRequest | None:
    return (
        TripUpdateRequest.query.filter_by(trip_id=trip_id, status="pending")
        .order_by(TripUpdateRequest.created_at.desc())
        .first()
    )


def approve_trip_update_request(request_row: TripUpdateRequest, reviewer_id: int) -> Trip:
    trip: Trip = request_row.trip
    trip.status = request_row.proposed_status
    regenerate_trip(
        trip,
        service_charge=float(request_row.proposed_service_charge or 0),
        number_of_days=int(request_row.proposed_number_of_days or trip.number_of_days),
        number_of_people=int(request_row.proposed_number_of_people or trip.number_of_people),
        places_per_day=int(request_row.proposed_places_per_day or 4),
    )
    request_row.status = "approved"
    request_row.reviewer_id = reviewer_id
    request_row.reviewed_at = datetime.utcnow()
    db.session.commit()
    return trip


def reject_trip_update_request(request_row: TripUpdateRequest, reviewer_id: int) -> Trip:
    trip: Trip = request_row.trip
    request_row.status = "rejected"
    request_row.reviewer_id = reviewer_id
    request_row.reviewed_at = datetime.utcnow()
    if not TripUpdateRequest.query.filter_by(trip_id=trip.id, status="pending").first():
        trip.status = "confirmed"
    db.session.commit()
    return trip
