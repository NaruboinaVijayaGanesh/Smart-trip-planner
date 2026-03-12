from functools import wraps

from flask import abort
from flask_login import current_user


def role_required(role: str):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role != role:
                abort(403)
            return view(*args, **kwargs)

        return wrapped_view

    return decorator


def trip_access_required(trip):
    if current_user.role == "agent":
        return True
    if current_user.role == "traveler" and trip.traveler_id == current_user.id:
        return True
    abort(403)
