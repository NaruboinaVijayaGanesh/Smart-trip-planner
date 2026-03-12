from __future__ import annotations

import base64
import json
from urllib.parse import urlencode
from urllib.request import Request
from urllib.request import urlopen

from flask import current_app
from flask import url_for

from app.extensions import db
from app.models import NotificationLog, Trip

TIME_SLOT_ORDER = {
    "Early Morning": 0,
    "Morning": 1,
    "Afternoon": 2,
    "Evening": 3,
    "Night": 4,
    "Late Night": 5,
}


def _normalize_phone(phone: str | None) -> str | None:
    raw = (phone or "").strip()
    if not raw:
        return None
    digits = "".join(ch for ch in raw if ch.isdigit() or ch == "+")
    if not digits:
        return None
    if not digits.startswith("+"):
        digits = f"+{digits}"
    return digits


def send_whatsapp_message(
    phone: str | None,
    message: str,
    content_sid: str | None = None,
    content_variables: dict[str, str] | None = None,
) -> tuple[bool, str]:
    to_phone = _normalize_phone(phone)
    if not to_phone:
        return False, "Missing phone number."

    account_sid = current_app.config.get("TWILIO_ACCOUNT_SID")
    auth_token = current_app.config.get("TWILIO_AUTH_TOKEN")
    from_number = _normalize_phone(current_app.config.get("TWILIO_WHATSAPP_FROM"))
    timeout = int(current_app.config.get("TWILIO_TIMEOUT_SECONDS", 12) or 12)

    if not (account_sid and auth_token and from_number):
        return False, "WhatsApp provider not configured."

    endpoint = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    payload_data = {
        "To": f"whatsapp:{to_phone}",
        "From": f"whatsapp:{from_number}",
    }
    if content_sid:
        payload_data["ContentSid"] = content_sid
        payload_data["ContentVariables"] = json.dumps(content_variables or {})
    else:
        payload_data["Body"] = message

    payload = urlencode(payload_data).encode("utf-8")
    token = base64.b64encode(f"{account_sid}:{auth_token}".encode("utf-8")).decode("utf-8")

    request = Request(
        endpoint,
        data=payload,
        headers={
            "Authorization": f"Basic {token}",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "ai-air-trip-planner/1.0 (+https://localhost)",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        sid = str(data.get("sid", "")).strip()
        return True, sid or "ok"
    except Exception as exc:
        current_app.logger.warning("WhatsApp send failed: %s", exc)
        return False, "Unable to send WhatsApp notification."


def _trip_url_for_message(trip: Trip) -> str:
    base_url = (current_app.config.get("APP_BASE_URL") or "").strip().rstrip("/")
    if trip.traveler_id:
        path = url_for("traveler.view_trip", trip_id=trip.id, _external=False)
    else:
        path = url_for("agent.view_trip", trip_id=trip.id, _external=False)
    if base_url:
        return f"{base_url}{path}"
    return path


def send_trip_whatsapp_notifications(trip: Trip, event_label: str) -> tuple[int, int]:
    message = (
        f"AI Air Trip Planner Update: {event_label}\n"
        f"Trip: {trip.title}\n"
        f"Route: {trip.destinations_raw}\n"
        f"Dates: {trip.start_date} for {trip.number_of_days} day(s)\n"
        f"Travelers: {trip.number_of_people}\n"
        f"Status: {trip.status}\n"
        f"Estimated total: {round(float(trip.total_group_cost or 0), 2)}\n"
        f"Details: {_trip_url_for_message(trip)}"
    )
    content_sid = current_app.config.get("TWILIO_CONTENT_SID")
    content_variables = None
    if content_sid:
        content_variables = {
            "1": str(trip.start_date),
            "2": current_app.config.get("TWILIO_TEMPLATE_TIME", "3pm"),
        }

    targets = []
    if trip.traveler and trip.traveler.phone and bool(getattr(trip.traveler, "whatsapp_opt_in", True)):
        targets.append(trip.traveler.phone)
    if trip.client and trip.client.phone:
        targets.append(trip.client.phone)

    unique_targets = []
    seen = set()
    for phone in targets:
        normalized = _normalize_phone(phone)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique_targets.append(normalized)

    sent = 0
    for phone in unique_targets:
        ok, provider_result = send_whatsapp_message(
            phone=phone,
            message=message,
            content_sid=content_sid,
            content_variables=content_variables,
        )
        db.session.add(
            NotificationLog(
                trip_id=trip.id,
                target_phone=phone,
                channel="whatsapp",
                event_label=event_label,
                status="sent" if ok else "failed",
                provider_message_id=provider_result if ok else None,
                error_message=None if ok else provider_result,
            )
        )
        if ok:
            sent += 1
    if unique_targets:
        db.session.commit()
    return sent, len(unique_targets)


def send_trip_summary_to_traveler(trip: Trip, requested_by: str | None = None) -> tuple[bool, str]:
    traveler = trip.traveler
    if not traveler:
        return False, "Trip is not linked to a traveler account."
    if not traveler.phone:
        return False, "Traveler phone number is missing."
    if not bool(getattr(traveler, "whatsapp_opt_in", True)):
        return False, "Traveler has disabled WhatsApp updates."

    destination_names = []
    for destination in sorted(trip.destinations, key=lambda item: item.order_index):
        name = (destination.name or "").strip()
        if name:
            destination_names.append(name)
    route_text = ", ".join(destination_names) if destination_names else (trip.destinations_raw or "-")

    itinerary_lines = []
    for item in sorted(
        trip.itineraries,
        key=lambda row: (row.day_number, TIME_SLOT_ORDER.get(row.time_slot, 99), row.time_slot),
    ):
        slot = (item.time_slot or "Anytime").strip()
        title = (item.title or "Planned activity").strip()
        ticket = round(float(item.ticket_price or 0), 2)
        itinerary_lines.append(f"D{item.day_number} {slot}: {title} (Ticket {ticket})")

    booking_lines = []
    for booking in sorted(trip.bookings, key=lambda row: row.created_at):
        hotel_name = booking.hotel.name if booking.hotel else "Hotel"
        booking_lines.append(
            f"{hotel_name} [{booking.status}/{booking.payment_status}] Total {round(float(booking.total_price or 0), 2)}"
        )

    requested_by_text = requested_by.strip() if requested_by else "your agent"
    message_parts = [
        "AI Air Trip Planner - Full Trip Summary",
        f"Shared by: {requested_by_text}",
        f"Trip: {trip.title}",
        f"Status: {trip.status}",
        f"Route: {route_text}",
        f"Start date: {trip.start_date}",
        f"Days: {trip.number_of_days}",
        f"Travelers: {trip.number_of_people}",
        f"Service charge: {round(float(trip.service_charge or 0), 2)}",
        f"Transport: {round(float(trip.transport_cost or 0), 2)}",
        f"Hotel: {round(float(trip.hotel_cost or 0), 2)}",
        f"Food: {round(float(trip.food_cost or 0), 2)}",
        f"Activity: {round(float(trip.activity_cost or 0), 2)}",
        f"Per person: {round(float(trip.per_person_cost or 0), 2)}",
        f"Total group: {round(float(trip.total_group_cost or 0), 2)}",
        f"Details: {_trip_url_for_message(trip)}",
    ]
    if itinerary_lines:
        message_parts.append("Itinerary:")
        message_parts.extend(itinerary_lines)
    if booking_lines:
        message_parts.append("Bookings:")
        message_parts.extend(booking_lines)

    max_len = 3200
    message = "\n".join(message_parts)
    if len(message) > max_len:
        truncated = []
        current_len = 0
        for line in message_parts:
            next_len = current_len + len(line) + 1
            if next_len > max_len - 50:
                break
            truncated.append(line)
            current_len = next_len
        truncated.append("... (message truncated)")
        message = "\n".join(truncated)

    ok, provider_result = send_whatsapp_message(phone=traveler.phone, message=message)
    db.session.add(
        NotificationLog(
            trip_id=trip.id,
            target_phone=_normalize_phone(traveler.phone),
            channel="whatsapp",
            event_label="Full trip summary sent by agent",
            status="sent" if ok else "failed",
            provider_message_id=provider_result if ok else None,
            error_message=None if ok else provider_result,
        )
    )
    db.session.commit()
    return ok, provider_result
