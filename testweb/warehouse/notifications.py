# shipments/notifications.py
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def notify_status_change(user, shipment, status, message):
    logger.info(f"Starting notify_status_change for user {user.email}, shipment {shipment.suit_number}, status {status}")
    # Email
    try:
        subject = f"Shipment {shipment.suit_number} status update: {status}"
        body = f"Hello {user.get_full_name() or user.username},\n\n"
        body += f"Your shipment {shipment.suit_number} ({shipment.tracking_number}) status changed to: {status}\n\n"
        if message:
            body += f"Update: {message}\n\n"
        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        body += f"View details: {site_url}/shipments/{shipment.id}/\n\nThanks."
        logger.info(f"Sending email to {user.email} with subject {subject}")
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
        logger.info(f"Email sent successfully to {user.email}")
    except Exception as exc:
        logger.exception("Failed sending status email: %s", exc)
    # TODO: integrate SMS or WhatsApp provider (Twilio, Vonage, etc.)
    # Example placeholder:
    logger.info("Notifying user %s via other channels (TODO)", user.username)