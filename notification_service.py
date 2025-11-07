from __future__ import annotations

import logging
from typing import Dict

from config import load_config

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self) -> None:
        cfg = load_config().get("notification", {})
        self.providers = {
            "email": cfg.get("emailProvider", "sendgrid"),
            "sms": cfg.get("smsProvider", "twilio"),
        }
        self.admin_email = cfg.get("adminEmail", "ops@example.com")

    def send_email(self, to: str, subject: str, body: str) -> None:
        logger.info("[Email->%s] %s", to, subject)
        logger.debug(body)

    def send_sms(self, to: str, body: str) -> None:
        logger.info("[SMS->%s] %s", to, body)

    def send_push(self, user_id: str, body: str) -> None:
        logger.info("[PUSH->%s] %s", user_id, body)

    def notify_user(self, user: Dict[str, str], message: str, channel: str = "email") -> None:
        contact = user.get("email") if channel == "email" else user.get("phone")
        if channel == "email" and contact:
            self.send_email(contact, "ArcPay update", message)
        elif channel == "sms" and contact:
            self.send_sms(contact, message)
        else:
            logger.warning("No contact for user %s on %s", user.get("userId"), channel)

    def notify_admin(self, subject: str, body: str) -> None:
        self.send_email(self.admin_email, subject, body)


__all__ = ["NotificationService"]
