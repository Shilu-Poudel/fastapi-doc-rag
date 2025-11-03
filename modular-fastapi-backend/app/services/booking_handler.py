from dataclasses import dataclass
from typing import Optional, Dict, Any
import re
from app.utils.db import Booking, get_db_session

@dataclass
class BookingResult:
    id: int
    name: str
    email: str
    date: str
    time: str

class BookingHandler:
    """
    Detects booking intent, extracts booking info, and persists to DB.
    """

    BOOKING_PHRASES = [
        "book an interview",
        "book interview",
        "schedule an interview",
        "i want to book an interview",
        "i want to schedule an interview",
    ]

    def detect_booking_intent(self, text: str) -> bool:
        """Return True if text likely indicates booking intent."""
        lowered = text.lower()
        return any(phrase in lowered for phrase in self.BOOKING_PHRASES)

    def extract_booking_details(self, text: str) -> Optional[Dict[str, str]]:
        """Extract name, email, date and time using simple regex heuristics."""
        email_re = r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"
        date_re = r"(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:,\s*\d{4})?)"
        time_re = r"(\d{1,2}:\d{2}(?:\s?[APap][Mm])?|\d{1,2}\s?(?:AM|PM|am|pm))"
        name_re = r"(?:name is|I'm|I am|this is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"

        email = re.search(email_re, text)
        date = re.search(date_re, text)
        time = re.search(time_re, text)
        name = re.search(name_re, text)

        if not email or not date or not time:
            # If required fields are missing, return None
            return None

        return {
            "name": name.group(1) if name else "Unknown",
            "email": email.group(1),
            "date": date.group(1),
            "time": time.group(1),
        }

    def save_booking(self, info: Dict[str, str]) -> BookingResult:
        """Persist booking into DB and return BookingResult."""
        session = get_db_session()
        booking = Booking(name=info["name"], email=info["email"], date=info["date"], time=info["time"])
        session.add(booking)
        session.commit()
        session.refresh(booking)
        return BookingResult(id=booking.id, name=booking.name, email=booking.email, date=booking.date, time=booking.time)