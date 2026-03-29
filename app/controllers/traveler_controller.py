from datetime import datetime, timedelta

from flask import Blueprint, abort, current_app, flash, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import OperationalError

from app.extensions import db
from app.models import Booking, Hotel, ItineraryEditRequest, Trip, TripUpdateRequest, User
from app.services.authz import role_required
from app.services.form_service import parse_trip_form, validate_trip_payload
from app.services.food_data_service import append_food_feedback
from app.services.hotel_service import get_live_hotel_availability, recommended_hotels
from app.services.itinerary_approval_service import approve_all_pending_requests, approve_request, reject_request
from app.services.place_service import build_destination_cards
from app.services.trip_service import (
    create_trip_from_form,
    ensure_trip_cost_floor_values,
    infer_places_per_day,
    parse_destinations,
    regenerate_trip,
)
from app.services.trip_update_approval_service import approve_trip_update_request, reject_trip_update_request
from app.services.weather_service import get_live_weather
from app.services.whatsapp_service import send_trip_whatsapp_notifications
from app.services.packing_service import generate_ai_packing_list
from app.services.food_recommendation_service import generate_local_food_guide
from app.services.export_service import generate_trip_pdf, generate_trip_ics


traveler_bp = Blueprint("traveler", __name__)
TIME_SLOT_ORDER = {
    "Early Morning": 0,
    "Morning": 1,
    "Afternoon": 2,
    "Evening": 3,
    "Night": 4,
    "Late Night": 5,
}


def _itinerary_sort_key(item):
    return (item.day_number, TIME_SLOT_ORDER.get(item.time_slot, 99), item.time_slot)


@traveler_bp.route("/dashboard")
@login_required
@role_required("traveler")
def dashboard():
    trips = Trip.query.filter_by(traveler_id=current_user.id).order_by(Trip.created_at.desc()).all()
    all_agents = User.query.filter_by(role="agent").order_by(User.full_name.asc()).all()
    upcoming = [trip for trip in trips if trip.status in {"draft", "sent", "confirmed", "in_progress"}]
    total_spent = sum(trip.total_group_cost for trip in trips)
    return render_template(
        "traveler/dashboard.html",
        trips=trips[:4],
        total_trips=len(trips),
        upcoming_trips=len(upcoming),
        total_spent=round(total_spent, 2),
        all_agents=all_agents,
    )


@traveler_bp.route("/trips")
@login_required
@role_required("traveler")
def my_trips():
    trips = Trip.query.filter_by(traveler_id=current_user.id).order_by(Trip.created_at.desc()).all()
    return render_template("traveler/my_trips.html", trips=trips)


@traveler_bp.route("/trips/new", methods=["GET", "POST"])
@login_required
@role_required("traveler")
def create_trip():
    all_agents = User.query.filter_by(role="agent").order_by(User.full_name.asc()).all()

    if request.method == "POST":
        try:
            payload = parse_trip_form(request.form)
        except ValueError:
            flash("Invalid input values. Please review the form.", "danger")
            return redirect(url_for("traveler.create_trip"))

        is_valid, message = validate_trip_payload(payload)
        if not is_valid:
            flash(message, "danger")
            return redirect(url_for("traveler.create_trip"))

        selected_agent_id = request.form.get("agent_id")
        if not selected_agent_id:
            flash("Agent selection is required.", "danger")
            return redirect(url_for("traveler.create_trip"))
        try:
            selected_agent_id_int = int(selected_agent_id)
        except ValueError:
            flash("Invalid agent selected.", "danger")
            return redirect(url_for("traveler.create_trip"))
        agent = User.query.filter_by(id=selected_agent_id_int, role="agent").first()
        if not agent:
            flash("Please choose a valid agent profile.", "danger")
            return redirect(url_for("traveler.create_trip"))
        selected_agent_id = agent.id

        try:
            trip = create_trip_from_form(payload, traveler_id=current_user.id, agent_id=selected_agent_id)
        except RuntimeError as exc:
            db.session.rollback()
            flash(str(exc), "danger")
            return redirect(url_for("traveler.create_trip"))
        except OperationalError as exc:
            db.session.rollback()
            current_app.logger.warning("Trip create failed due to DB operational error: %s", exc)
            flash("Database is busy. Please try generating again in a few seconds.", "danger")
            return redirect(url_for("traveler.create_trip"))
        sent, targets = send_trip_whatsapp_notifications(trip, "Trip created")
        if targets:
            current_app.logger.info("Traveler trip create WhatsApp sent to %s/%s targets", sent, targets)
        flash("Trip generated successfully.", "success")
        return redirect(url_for("traveler.view_trip", trip_id=trip.id))

    return render_template("traveler/create_trip.html", all_agents=all_agents)


@traveler_bp.route("/trips/<int:trip_id>")
@login_required
@role_required("traveler")
def view_trip(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if trip.traveler_id != current_user.id:
        abort(403)

    cost_repaired = ensure_trip_cost_floor_values(trip)
    destinations = parse_destinations(trip.destinations_raw)
    checkin_date = trip.start_date.isoformat()
    checkout_date = (trip.start_date + timedelta(days=max(1, int(trip.number_of_days)))).isoformat()
    hotels = recommended_hotels(
        destinations,
        state_country=trip.state_country,
        persist=True,
        checkin_date=checkin_date,
        checkout_date=checkout_date,
    )
    weather_updated = False
    for item in trip.itineraries:
        existing = (item.weather_summary or "").strip()
        if (
            (not existing)
            or ("Live weather API can be plugged here" in existing)
            or ("Weather currently unavailable" in existing)
            or ("Weather estimate not available now" in existing)
        ):
            destination_name = item.destination.name if item.destination else (destinations[0] if destinations else trip.state_country)
            weather_data = get_live_weather(
                destination_name,
                trip.start_date,
                max(0, item.day_number - 1),
                provider=current_app.config.get("WEATHER_PROVIDER", "open-meteo"),
            )
            item.weather_summary = weather_data["summary"]
            weather_updated = True
    if weather_updated:
        db.session.commit()
    elif cost_repaired:
        db.session.commit()

    itinerary_by_day = {}
    for item in sorted(trip.itineraries, key=_itinerary_sort_key):
        itinerary_by_day.setdefault(item.day_number, []).append(item)
    destination_cards = build_destination_cards(
        destinations,
        state_country=trip.state_country,
        google_places_api_key=None,
    )
    budget_gap = round(trip.total_group_cost - trip.budget, 2)
    within_budget = budget_gap <= 0
    bookings = sorted(trip.bookings, key=lambda x: x.created_at, reverse=True)
    booking_form_action = f"/traveler/trips/{trip.id}/bookings"
    pending_requests = (
        ItineraryEditRequest.query.filter_by(trip_id=trip.id, status="pending")
        .order_by(ItineraryEditRequest.created_at.asc())
        .all()
    )
    pending_trip_update = (
        TripUpdateRequest.query.filter_by(trip_id=trip.id, status="pending")
        .order_by(TripUpdateRequest.created_at.desc())
        .first()
    )

    return render_template(
        "traveler/trip_detail.html",
        trip=trip,
        itinerary_by_day=itinerary_by_day,
        hotels=hotels,
        destinations=destinations,
        destination_cards=destination_cards,
        budget_gap=budget_gap,
        within_budget=within_budget,
        bookings=bookings,
        booking_form_action=booking_form_action,
        places_per_day=infer_places_per_day(trip, fallback=4),
        pending_requests=pending_requests,
        pending_trip_update=pending_trip_update,
    )


@traveler_bp.route("/trips/<int:trip_id>/regenerate", methods=["POST"])
@login_required
@role_required("traveler")
def regenerate(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if trip.traveler_id != current_user.id:
        abort(403)

    keep_days_raw = request.form.getlist("keep_days")
    keep_days = set()
    for value in keep_days_raw:
        try:
            keep_days.add(int(value))
        except ValueError:
            continue

    number_of_days = request.form.get("number_of_days", "").strip()
    number_of_people = request.form.get("number_of_people", "").strip()
    places_per_day = request.form.get("places_per_day", "").strip()

    try:
        updated_days = int(number_of_days or trip.number_of_days)
        updated_people = int(number_of_people or trip.number_of_people)
        updated_places_per_day = int(places_per_day or infer_places_per_day(trip, fallback=4))
    except ValueError:
        flash("Invalid regenerate inputs.", "danger")
        return redirect(url_for("traveler.view_trip", trip_id=trip.id))

    destinations = parse_destinations(trip.destinations_raw)
    if updated_days < len(destinations):
        flash("Number of days must be at least equal to destination count.", "danger")
        return redirect(url_for("traveler.view_trip", trip_id=trip.id))
    if updated_days <= 0 or updated_people <= 0:
        flash("Days and travelers must be greater than zero.", "danger")
        return redirect(url_for("traveler.view_trip", trip_id=trip.id))
    if updated_places_per_day < 3 or updated_places_per_day > 6:
        flash("Places per day must be between 3 and 6.", "danger")
        return redirect(url_for("traveler.view_trip", trip_id=trip.id))

    try:
        regenerate_trip(
            trip,
            keep_days=keep_days,
            number_of_days=updated_days,
            number_of_people=updated_people,
            places_per_day=updated_places_per_day,
        )
    except RuntimeError as exc:
        db.session.rollback()
        flash(str(exc), "danger")
        return redirect(url_for("traveler.view_trip", trip_id=trip.id))
    except OperationalError as exc:
        db.session.rollback()
        current_app.logger.warning("Trip regenerate failed due to DB operational error: %s", exc)
        flash("Database is busy. Please retry regenerate after a few seconds.", "danger")
        return redirect(url_for("traveler.view_trip", trip_id=trip.id))
    sent, targets = send_trip_whatsapp_notifications(trip, "Trip itinerary regenerated")
    if targets:
        current_app.logger.info("Traveler trip regenerate WhatsApp sent to %s/%s targets", sent, targets)
    flash("Itinerary regenerated.", "success")
    return redirect(url_for("traveler.view_trip", trip_id=trip.id))


@traveler_bp.route("/trips/<int:trip_id>/approve", methods=["POST"])
@login_required
@role_required("traveler")
def approve_trip(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if trip.traveler_id != current_user.id:
        abort(403)

    pending_update = (
        TripUpdateRequest.query.filter_by(trip_id=trip.id, status="pending")
        .order_by(TripUpdateRequest.created_at.desc())
        .first()
    )
    if pending_update:
        approve_trip_update_request(pending_update, reviewer_id=current_user.id)

    approved_count = approve_all_pending_requests(trip, reviewer_id=current_user.id)
    send_trip_whatsapp_notifications(trip, "Traveler approved itinerary changes")
    if approved_count:
        flash(f"Approved {approved_count} pending itinerary change(s).", "success")
    else:
        trip.status = "confirmed"
        db.session.commit()
        flash("Trip status set to confirmed.", "success")
    return redirect(url_for("traveler.view_trip", trip_id=trip.id))


@traveler_bp.route("/trip-update-requests/<int:request_id>/approve", methods=["POST"])
@login_required
@role_required("traveler")
def approve_trip_update(request_id):
    update_request = TripUpdateRequest.query.get_or_404(request_id)
    trip = Trip.query.get_or_404(update_request.trip_id)
    if trip.traveler_id != current_user.id:
        abort(403)
    if update_request.status != "pending":
        flash("This update request is already reviewed.", "warning")
        return redirect(url_for("traveler.view_trip", trip_id=trip.id))

    approve_trip_update_request(update_request, reviewer_id=current_user.id)
    send_trip_whatsapp_notifications(trip, "Traveler approved trip update request")
    flash("Trip update request approved and applied.", "success")
    return redirect(url_for("traveler.view_trip", trip_id=trip.id))


@traveler_bp.route("/trip-update-requests/<int:request_id>/reject", methods=["POST"])
@login_required
@role_required("traveler")
def reject_trip_update(request_id):
    update_request = TripUpdateRequest.query.get_or_404(request_id)
    trip = Trip.query.get_or_404(update_request.trip_id)
    if trip.traveler_id != current_user.id:
        abort(403)
    if update_request.status != "pending":
        flash("This update request is already reviewed.", "warning")
        return redirect(url_for("traveler.view_trip", trip_id=trip.id))

    reject_trip_update_request(update_request, reviewer_id=current_user.id)
    send_trip_whatsapp_notifications(trip, "Traveler rejected trip update request")
    flash("Trip update request rejected.", "info")
    return redirect(url_for("traveler.view_trip", trip_id=trip.id))


@traveler_bp.route("/itinerary-requests/<int:request_id>/approve", methods=["POST"])
@login_required
@role_required("traveler")
def approve_itinerary_request(request_id):
    edit_request = ItineraryEditRequest.query.get_or_404(request_id)
    trip = Trip.query.get_or_404(edit_request.trip_id)
    if trip.traveler_id != current_user.id:
        abort(403)
    if edit_request.status != "pending":
        flash("This request is already reviewed.", "warning")
        return redirect(url_for("traveler.view_trip", trip_id=trip.id))

    approve_request(edit_request, reviewer_id=current_user.id)
    send_trip_whatsapp_notifications(trip, "Traveler approved one itinerary change")
    flash("Itinerary change approved.", "success")
    return redirect(url_for("traveler.view_trip", trip_id=trip.id))


@traveler_bp.route("/itinerary-requests/<int:request_id>/reject", methods=["POST"])
@login_required
@role_required("traveler")
def reject_itinerary_request(request_id):
    edit_request = ItineraryEditRequest.query.get_or_404(request_id)
    trip = Trip.query.get_or_404(edit_request.trip_id)
    if trip.traveler_id != current_user.id:
        abort(403)
    if edit_request.status != "pending":
        flash("This request is already reviewed.", "warning")
        return redirect(url_for("traveler.view_trip", trip_id=trip.id))

    reject_request(edit_request, reviewer_id=current_user.id)
    send_trip_whatsapp_notifications(trip, "Traveler rejected one itinerary change")
    flash("Itinerary change rejected.", "info")
    return redirect(url_for("traveler.view_trip", trip_id=trip.id))


@traveler_bp.route("/trips/<int:trip_id>/delete", methods=["POST"])
@login_required
@role_required("traveler")
def delete_trip(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if trip.traveler_id != current_user.id:
        abort(403)

    db.session.delete(trip)
    db.session.commit()
    flash("Trip deleted.", "info")
    return redirect(url_for("traveler.my_trips"))


@traveler_bp.route("/trips/<int:trip_id>/bookings", methods=["POST"])
@login_required
@role_required("traveler")
def create_booking(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if trip.traveler_id != current_user.id:
        abort(403)

    hotel_id = request.form.get("hotel_id")
    if not hotel_id:
        flash("Please choose a valid hotel to book.", "danger")
        return redirect(url_for("traveler.view_trip", trip_id=trip.id))

    hotel = Hotel.query.get_or_404(int(hotel_id))
    checkin = request.form.get("checkin_date")
    checkout = request.form.get("checkout_date")

    if not checkin or not checkout:
        flash("Check-in and check-out dates are required.", "danger")
        return redirect(url_for("traveler.view_trip", trip_id=trip.id))

    try:
        checkin_date = datetime.strptime(checkin, "%Y-%m-%d").date()
        checkout_date = datetime.strptime(checkout, "%Y-%m-%d").date()
    except ValueError:
        flash("Invalid booking dates.", "danger")
        return redirect(url_for("traveler.view_trip", trip_id=trip.id))

    if checkout_date <= checkin_date:
        flash("Check-out date must be after check-in date.", "danger")
        return redirect(url_for("traveler.view_trip", trip_id=trip.id))

    booking = Booking(
        trip_id=trip.id,
        hotel_id=hotel.id,
        client_id=trip.client_id,
        checkin_date=checkin_date,
        checkout_date=checkout_date,
        reference_number=request.form.get("reference_number", "").strip() or None,
        status="pending",
        payment_status="pending",
        total_price=float(request.form.get("total_price", 0) or 0),
    )

    availability_status, _rooms = get_live_hotel_availability(
        hotel_name=hotel.name,
        city=hotel.city,
        state_country=trip.state_country,
        checkin_date=checkin_date.isoformat(),
        checkout_date=checkout_date.isoformat(),
    )
    if availability_status == "Sold Out":
        flash("Selected hotel is sold out for the chosen dates. Please pick another hotel.", "danger")
        return redirect(url_for("traveler.view_trip", trip_id=trip.id))

    db.session.add(booking)
    db.session.commit()
    sent, targets = send_trip_whatsapp_notifications(trip, "Hotel booking created")
    if targets:
        current_app.logger.info("Traveler booking WhatsApp sent to %s/%s targets", sent, targets)
    flash("Booking created successfully.", "success")
    return redirect(url_for("traveler.view_trip", trip_id=trip.id))


@traveler_bp.route("/trips/<int:trip_id>/food-feedback", methods=["POST"])
@login_required
@role_required("traveler")
def submit_food_feedback(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if trip.traveler_id != current_user.id:
        abort(403)

    actual_food_cost_raw = request.form.get("actual_food_cost", "").strip()
    actual_total_cost_raw = request.form.get("actual_total_cost", "").strip()
    if not actual_food_cost_raw:
        flash("Please enter actual food cost.", "danger")
        return redirect(url_for("traveler.view_trip", trip_id=trip.id))

    try:
        actual_food_cost = float(actual_food_cost_raw)
        actual_total_cost = float(actual_total_cost_raw) if actual_total_cost_raw else None
    except ValueError:
        flash("Invalid numeric values for actual costs.", "danger")
        return redirect(url_for("traveler.view_trip", trip_id=trip.id))

    if actual_food_cost <= 0:
        flash("Actual food cost must be greater than zero.", "danger")
        return redirect(url_for("traveler.view_trip", trip_id=trip.id))

    append_food_feedback(
        trip,
        actual_food_cost=actual_food_cost,
        actual_total_cost=actual_total_cost,
        source_role="traveler",
    )
    flash("Thanks. Real food-cost data saved for ML training.", "success")
    return redirect(url_for("traveler.view_trip", trip_id=trip.id))


@traveler_bp.route("/trips/<int:trip_id>/packing/generate", methods=["POST"])
@login_required
@role_required("traveler")
def generate_packing(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if trip.traveler_id != current_user.id:
        abort(403)

    items = generate_ai_packing_list(trip)
    if not items:
        flash("Could not generate packing list. Please try again later.", "warning")
    else:
        trip.packing_list = items
        db.session.commit()
        flash("AI Packing Checklist generated!", "success")

    return redirect(url_for("traveler.view_trip", trip_id=trip.id))


@traveler_bp.route("/trips/<int:trip_id>/packing/toggle", methods=["POST"])
@login_required
@role_required("traveler")
def toggle_packing_item(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if trip.traveler_id != current_user.id:
        abort(403)

    item_id = request.form.get("item_id")
    if not item_id:
        return redirect(url_for("traveler.view_trip", trip_id=trip.id))

    current_list = trip.packing_list
    updated = False
    for it in current_list:
        if it.get("id") == item_id:
            it["checked"] = not it.get("checked", False)
            updated = True
            break
    
    if updated:
        trip.packing_list = current_list
        db.session.commit()
    
    # Check if it's an AJAX request
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return {"success": True}

    return redirect(url_for("traveler.view_trip", trip_id=trip.id))


@traveler_bp.route("/trips/<int:trip_id>/packing/reset", methods=["POST"])
@login_required
@role_required("traveler")
def reset_packing(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if trip.traveler_id != current_user.id:
        abort(403)

    trip.packing_list = []
    db.session.commit()
    flash("Packing checklist cleared.", "info")
    return redirect(url_for("traveler.view_trip", trip_id=trip.id))


@traveler_bp.route("/trips/<int:trip_id>/food/generate", methods=["POST"])
@login_required
@role_required("traveler")
def generate_food_guide(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if trip.traveler_id != current_user.id:
        abort(403)

    guide = generate_local_food_guide(trip)
    if not guide:
        flash("Could not generate food guide. Please try again later.", "warning")
    else:
        trip.food_deep_dive = guide
        db.session.commit()
        flash("Local food guide generated!", "success")

    return redirect(url_for("traveler.view_trip", trip_id=trip.id))


@traveler_bp.route("/trips/<int:trip_id>/food/reset", methods=["POST"])
@login_required
@role_required("traveler")
def reset_food_guide(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if trip.traveler_id != current_user.id:
        abort(403)

    trip.food_deep_dive = []
    db.session.commit()
    flash("Food guide cleared.", "info")
    return redirect(url_for("traveler.view_trip", trip_id=trip.id))


@traveler_bp.route("/trips/<int:trip_id>/export/pdf")
@login_required
@role_required("traveler")
def export_pdf(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if trip.traveler_id != current_user.id:
        abort(403)

    itinerary_by_day = {}
    for item in sorted(trip.itineraries, key=_itinerary_sort_key):
        itinerary_by_day.setdefault(item.day_number, []).append(item)

    pdf_bytes = generate_trip_pdf(trip, itinerary_by_day)
    
    response = make_response(pdf_bytes)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename=itinerary_{trip.id}.pdf"
    return response


@traveler_bp.route("/trips/<int:trip_id>/export/ics")
@login_required
@role_required("traveler")
def export_ics(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if trip.traveler_id != current_user.id:
        abort(403)

    ics_bytes = generate_trip_ics(trip)
    
    response = make_response(ics_bytes)
    response.headers["Content-Type"] = "text/calendar"
    response.headers["Content-Disposition"] = f"attachment; filename=itinerary_{trip.id}.ics"
    return response


@traveler_bp.route("/trips/<int:trip_id>/share/whatsapp", methods=["POST"])
@login_required
@role_required("traveler")
def share_whatsapp(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if trip.traveler_id != current_user.id:
        abort(403)

    if not trip.traveler.phone:
        flash("Please update your profile with a valid phone number first.", "warning")
        return redirect(url_for("traveler.view_trip", trip_id=trip.id))

    sent_count, target_count = send_trip_whatsapp_notifications(trip, "Itinerary shared manually by you")
    if sent_count > 0:
        flash(f"Itinerary shared to your WhatsApp (+{trip.traveler.phone})!", "success")
    else:
        # Check if Twilio is configured
        if not current_app.config.get("TWILIO_ACCOUNT_SID"):
            flash("WhatsApp service is not fully configured on the server yet.", "info")
        else:
            flash("Failed to send WhatsApp message. Please check your phone number.", "danger")

    return redirect(url_for("traveler.view_trip", trip_id=trip.id))
