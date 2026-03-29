import re
import socket
from functools import lru_cache
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json


EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z\s'.-]{1,118}$")
LOCATION_PATTERN = re.compile(r"^[A-Za-z][A-Za-z\s,.'-]{1,118}$")
PHONE_PATTERN = re.compile(r"^\+?[0-9][0-9\s-]{6,18}$")


@lru_cache(maxsize=512)
def _geocode_exists(name: str) -> bool:
    """Return True if 'name' resolves to at least one known location via Open-Meteo geocoding."""
    try:
        params = urlencode({"name": name, "count": 1, "language": "en", "format": "json"})
        req = Request(
            f"https://geocoding-api.open-meteo.com/v1/search?{params}",
            headers={"User-Agent": "ai-air-trip-planner/1.0 (+https://localhost)"},
        )
        with urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
        results = data.get("results") or []
        return len(results) > 0
    except Exception:
        # If geocoding is unavailable (network error, timeout) – accept the input
        # to avoid blocking the form on API outages.
        return True


@lru_cache(maxsize=512)
def _geocode_country(name: str, hint: str | None = None) -> str | None:
    """Return the ISO2 country code for `name`, or None if unavailable/ambiguous."""
    try:
        query = f"{name}, {hint}" if hint else name
        params = urlencode({"name": query, "count": 1, "language": "en", "format": "json"})
        req = Request(
            f"https://geocoding-api.open-meteo.com/v1/search?{params}",
            headers={"User-Agent": "ai-air-trip-planner/1.0 (+https://localhost)"},
        )
        with urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
        results = data.get("results") or []
        if results:
            return (results[0].get("country_code") or "").upper() or None
        return None
    except Exception:
        return None


def destinations_share_same_country(destinations: list[str], hint: str | None = None) -> tuple[bool, str]:
    """
    Verify all destinations belong to the same country.
    Returns (True, "") when they do, or (False, error_message) when they don't.
    Skips the check gracefully if geocoding is unavailable for any destination.
    """
    if len(destinations) <= 1:
        return True, ""

    country_map: dict[str, str] = {}   # city -> country_code
    for dest in destinations:
        primary = dest.split(",")[0].strip()
        code = _geocode_country(primary, hint)
        if code:
            country_map[primary] = code

    unique_countries = set(country_map.values())
    if len(unique_countries) <= 1:
        # Either all same country, or geocoding returned nothing (fail-open)
        return True, ""

    # Build a readable list of which city maps to which country for the error message
    offenders = ", ".join(f"{city} ({code})" for city, code in country_map.items())
    return (
        False,
        f"All destinations must be in the same country. "
        f"Found destinations from different countries: {offenders}. "
        "Please plan separate trips for each country.",
    )


def normalize_email(value: str) -> str:
    return (value or "").strip().lower()


def is_valid_email(value: str) -> bool:
    return bool(EMAIL_PATTERN.fullmatch(normalize_email(value)))


def email_domain_resolves(value: str) -> bool:
    email = normalize_email(value)
    if not is_valid_email(email):
        return False
    domain = email.split("@", 1)[-1].strip().lower()
    try:
        socket.getaddrinfo(domain, None)
        return True
    except socket.gaierror:
        return False


def is_valid_full_name(value: str) -> bool:
    return bool(NAME_PATTERN.fullmatch((value or "").strip()))


def is_valid_location_text(value: str) -> bool:
    return bool(LOCATION_PATTERN.fullmatch((value or "").strip()))


def is_real_location(value: str) -> bool:
    """Return True only if the value passes text validation AND resolves via geocoding."""
    cleaned = (value or "").strip()
    if not is_valid_location_text(cleaned):
        return False
    # Only validate the primary city name (before first comma) for geocoding.
    primary = cleaned.split(",")[0].strip()
    return _geocode_exists(primary)


def is_valid_phone(value: str) -> bool:
    cleaned = (value or "").strip()
    if not cleaned:
        return True
    return bool(PHONE_PATTERN.fullmatch(cleaned))


def password_strength_errors(value: str) -> list[str]:
    password = value or ""
    errors = []
    if len(password) < 8:
        errors.append("at least 8 characters")
    if not re.search(r"[A-Z]", password):
        errors.append("one uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("one lowercase letter")
    if not re.search(r"[0-9]", password):
        errors.append("one number")
    if not re.search(r"[^A-Za-z0-9]", password):
        errors.append("one special character")
    return errors
