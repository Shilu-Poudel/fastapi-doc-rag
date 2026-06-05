import re
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import Booking
from app.services.email_service import send_booking_confirmation

# Disallows whitespace/newlines, which also prevents email header injection.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate(full_name: str, email: str, date: str, time: str) -> None:
    if not full_name.strip():
        raise ValueError("full_name is required")
    if not _EMAIL_RE.match(email):
        raise ValueError(f"invalid email address: {email!r}")
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("date must be in YYYY-MM-DD format")
    try:
        datetime.strptime(time, "%H:%M")
    except ValueError:
        raise ValueError("time must be in HH:MM 24-hour format")


def create_booking(
    db: Session, full_name: str, email: str, date: str, time: str
) -> Booking:
    """Validate, persist an interview booking and send a confirmation email."""
    _validate(full_name, email, date, time)
    booking = Booking(full_name=full_name, email=email, date=date, time=time)
    db.add(booking)
    db.commit()
    db.refresh(booking)
    send_booking_confirmation(email, full_name, date, time)
    return booking
