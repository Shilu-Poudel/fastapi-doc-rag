import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.core.logging import logger


def send_booking_confirmation(
    to_email: str, full_name: str, date: str, time: str
) -> bool:
    """Send an interview confirmation email over SMTP.

    Returns False (without raising) when SMTP is not configured, so booking
    persistence is never blocked by email delivery.
    """
    if not settings.smtp_host:
        logger.warning("SMTP not configured; skipping confirmation email")
        return False

    message = EmailMessage()
    message["Subject"] = "Interview Booking Confirmation"
    message["From"] = settings.smtp_from or settings.smtp_user
    message["To"] = to_email
    message.set_content(
        f"Hello {full_name},\n\n"
        f"Your interview has been booked for {date} at {time}.\n\n"
        "Regards,\nRecruitment Team"
    )

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            server.starttls()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(message)
        return True
    except Exception:
        logger.exception("Failed to send confirmation email to %s", to_email)
        return False
