import re
import socket


EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z\s'.-]{1,118}$")
LOCATION_PATTERN = re.compile(r"^[A-Za-z][A-Za-z\s,.'-]{1,118}$")
PHONE_PATTERN = re.compile(r"^\+?[0-9][0-9\s-]{6,18}$")


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
