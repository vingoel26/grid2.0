"""Service to send notifications (Email/SMS) to vehicle owners."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from ..core.config import settings
from .owner_lookup import OwnerInfo
from ..models import Violation

log = logging.getLogger("backend.notification")


class Notifier(ABC):
    @abstractmethod
    def send(self, challan_number: str, violation: Violation, owner: OwnerInfo, pdf_path: str | None, fine: int) -> bool:
        pass


class ConsoleNotifier(Notifier):
    """Fallback notifier that just logs to stdout. Useful for local dev."""
    def send(self, challan_number: str, violation: Violation, owner: OwnerInfo, pdf_path: str | None, fine: int) -> bool:
        log.info(f"\n{'='*50}\n"
                 f"NOTIFICATION DISPATCH (CONSOLE)\n"
                 f"To: {owner.name} (Phone: {owner.phone}, Email: {owner.email})\n"
                 f"Subject: Traffic Challan {challan_number}\n"
                 f"Message: You have been issued a challan for {violation.violation_type}.\n"
                 f"Fine: Rs. {fine}. Plate: {violation.plate_number}\n"
                 f"PDF: {pdf_path}\n"
                 f"{'='*50}\n")
        return True


class SMSNotifier(Notifier):
    """Twilio SMS notifier."""
    def __init__(self):
        self.sid = getattr(settings, 'twilio_sid', None)
        self.token = getattr(settings, 'twilio_token', None)
        self.from_no = getattr(settings, 'twilio_from', None)
        self.enabled = bool(self.sid and self.token and self.from_no)
        
        if self.enabled:
            try:
                from twilio.rest import Client
                self.client = Client(self.sid, self.token)
            except ImportError:
                log.warning("Twilio library not installed. SMS disabled.")
                self.enabled = False

    def send(self, challan_number: str, violation: Violation, owner: OwnerInfo, pdf_path: str | None, fine: int) -> bool:
        if not self.enabled:
            return False
        
        if not owner.phone:
            log.warning(f"Cannot send SMS for {challan_number}: No phone number")
            return False
            
        try:
            msg = (f"Traffic Alert: Challan {challan_number} issued for {violation.plate_number} "
                   f"({violation.violation_type}). Fine: Rs. {fine}. "
                   f"Check portal for details.")
            
            message = self.client.messages.create(
                body=msg,
                from_=self.from_no,
                to=owner.phone
            )
            log.info(f"Sent SMS for {challan_number} to {owner.phone}. SID: {message.sid}")
            return True
        except Exception as e:
            log.error(f"Failed to send SMS for {challan_number}: {e}")
            return False


class EmailNotifier(Notifier):
    """SMTP Email notifier."""
    def __init__(self):
        self.host = getattr(settings, 'smtp_host', None)
        self.port = getattr(settings, 'smtp_port', 587)
        self.user = getattr(settings, 'smtp_user', None)
        self.password = getattr(settings, 'smtp_password', None)
        self.enabled = bool(self.host and self.user)

    def send(self, challan_number: str, violation: Violation, owner: OwnerInfo, pdf_path: str | None, fine: int) -> bool:
        if not self.enabled:
            return False
            
        if not owner.email:
            log.warning(f"Cannot send Email for {challan_number}: No email address")
            return False
            
        # In a real app, use smtplib/email modules here to send the actual email with PDF attachment
        log.info(f"Simulating Email sent for {challan_number} to {owner.email} via {self.host}")
        return True


def get_notifiers() -> list[Notifier]:
    """Returns configured notifiers based on settings."""
    notifiers = []
    
    mode = getattr(settings, 'notification_mode', 'console')
    
    if mode == 'console':
        notifiers.append(ConsoleNotifier())
    else:
        # Live mode
        sms = SMSNotifier()
        if sms.enabled:
            notifiers.append(sms)
            
        email = EmailNotifier()
        if email.enabled:
            notifiers.append(email)
            
        # Fallback to console if nothing else is configured
        if not notifiers:
            log.warning("Notification mode is 'live' but no SMS/Email configured. Falling back to console.")
            notifiers.append(ConsoleNotifier())
            
    return notifiers


def notify_owner(challan_number: str, violation: Violation, owner: OwnerInfo, pdf_path: str | None, fine: int) -> list[str]:
    """
    Sends notifications to the owner.
    Returns a list of successful channels (e.g., ['SMS', 'EMAIL'] or ['CONSOLE']).
    """
    notifiers = get_notifiers()
    successes = []
    
    for n in notifiers:
        if n.send(challan_number, violation, owner, pdf_path, fine):
            if isinstance(n, ConsoleNotifier):
                successes.append("CONSOLE")
            elif isinstance(n, SMSNotifier):
                successes.append("SMS")
            elif isinstance(n, EmailNotifier):
                successes.append("EMAIL")
                
    return successes
