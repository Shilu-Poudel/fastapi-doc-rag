from dataclasses import dataclass
from typing import Optional, Dict, Any
import re
import json
from app.utils.db import Booking, get_db_session
from app.services.embeddings import call_groq_completion

@dataclass
class BookingResult:
    id: int
    name: str
    email: str
    date: str
    time: str

class BookingHandler:
    """
    Detects booking intent, extracts booking info using LLM, and persists to DB.
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
        """
        Extract name, email, date and time using LLM.
        Falls back to regex if LLM extraction fails.
        """
        # Try LLM-based extraction first
        llm_result = self._extract_with_llm(text)
        if llm_result:
            return llm_result
        
        # Fallback to regex if LLM fails
        return self._extract_with_regex(text)

    def _extract_with_llm(self, text: str) -> Optional[Dict[str, str]]:
        """Use LLM to extract booking details from text."""
        prompt = f"""Extract the booking information from the following text.
Return ONLY a valid JSON object with these exact keys: name, email, date, time.
If any information is missing, return null for that field.

Text: {text}

JSON (no additional text):"""

        try:
            response = call_groq_completion(prompt, max_tokens=200, temperature=0.0)
            
            # Try to parse JSON from response
            # Sometimes LLM adds markdown code blocks, so clean it
            response = response.strip()
            if response.startswith("```"):
                # Remove markdown code blocks
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
                response = response.strip()
            
            data = json.loads(response)
            
            # Validate required fields
            if data.get("email") and data.get("date") and data.get("time"):
                return {
                    "name": data.get("name") or "Unknown",
                    "email": data["email"],
                    "date": data["date"],
                    "time": data["time"],
                }
        except (json.JSONDecodeError, KeyError, Exception):
            # If LLM extraction fails, return None to trigger fallback
            pass
        
        return None

    def _extract_with_regex(self, text: str) -> Optional[Dict[str, str]]:
        """Fallback: Extract booking details using regex patterns."""
        email_re = r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"
        date_re = r"(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:,\s*\d{4})?)"
        time_re = r"(\d{1,2}:\d{2}(?:\s?[APap][Mm])?|\d{1,2}\s?(?:AM|PM|am|pm))"
        name_re = r"(?:name is|I'm|I am|this is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"

        email = re.search(email_re, text)
        date = re.search(date_re, text)
        time = re.search(time_re, text)
        name = re.search(name_re, text)

        if not email or not date or not time:
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