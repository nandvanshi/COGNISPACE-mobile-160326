"""
Notification Service - Centralized notification handling for WhatsApp and Email
"""
import logging
from typing import Optional
from datetime import datetime, timezone, timedelta

from services.whatsapp.service import WhatsAppService
from services.whatsapp.templates import (
    TEMPLATE_WELCOME,
    TEMPLATE_APPOINTMENT_CONFIRMED,
    TEMPLATE_APPOINTMENT_REMINDER,
    TEMPLATE_PAYMENT_RECEIVED,
    get_welcome_variables,
    get_appointment_confirmed_variables,
    get_appointment_reminder_variables,
    get_payment_received_variables,
)
from services.email.registry import EmailProviderRegistry
from services.email.base import EmailMessage
from services.email.templates import get_email_template

logger = logging.getLogger(__name__)


def format_date_ist(dt_str: str) -> str:
    """Format datetime string to IST date (DD/MM/YYYY)"""
    if not dt_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        ist_dt = dt + timedelta(hours=5, minutes=30)
        return ist_dt.strftime("%d/%m/%Y")
    except Exception:
        return dt_str


def format_time_ist(dt_str: str) -> str:
    """Format datetime string to IST time (HH:MM AM/PM)"""
    if not dt_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        ist_dt = dt + timedelta(hours=5, minutes=30)
        return ist_dt.strftime("%I:%M %p")
    except Exception:
        return dt_str


class NotificationService:
    """Centralized notification service for sending WhatsApp and Email notifications"""
    
    @staticmethod
    async def send_therapist_welcome(
        name: str,
        mobile: str,
        email: str,
        password: Optional[str],
        trial_end_date: str,
        login_url: str = "https://cognispace.in/login"
    ):
        """
        Send welcome notifications to newly approved therapist.
        - WhatsApp: Simple welcome message (template cogni_1st)
        - Email: Detailed welcome with credentials and platform guide
        """
        # Send WhatsApp - use name as-is (don't add Dr. prefix)
        try:
            result = await WhatsAppService.send_template_message(
                to_mobile=mobile,
                content_sid=TEMPLATE_WELCOME["sid"],
                content_variables=get_welcome_variables(name)
            )
            if result.success:
                logger.info(f"Welcome WhatsApp sent to therapist {mobile}")
            else:
                logger.warning(f"WhatsApp failed for therapist {mobile}: {result.error}")
        except Exception as e:
            logger.error(f"WhatsApp error for therapist {mobile}: {e}")
        
        # Send Email - detailed welcome with guide
        if email:
            try:
                template_data = {
                    "therapist_name": name,
                    "mobile": mobile,
                    "password": password,
                    "trial_end_date": trial_end_date,
                    "login_url": login_url,
                }
                email_content = get_email_template("therapist_welcome", template_data)
                message = EmailMessage(
                    to=email,
                    subject=email_content["subject"],
                    html_body=email_content["html_body"],
                    text_body=email_content["text_body"]
                )
                result = await EmailProviderRegistry.send_email(message)
                if result.success:
                    logger.info(f"Welcome email sent to therapist {email}")
                else:
                    logger.warning(f"Email failed for therapist {email}: {result.error}")
            except Exception as e:
                logger.error(f"Email error for therapist {email}: {e}")
    
    @staticmethod
    async def send_client_welcome(
        client_name: str,
        mobile: str,
        email: Optional[str],
        username: str,
        password: str,
        therapist_name: str,
        login_url: str = "https://cognispace.in/login"
    ):
        """
        Send welcome notifications to newly created client.
        - WhatsApp: Simple welcome message (template cogni_1st)
        - Email: Detailed welcome with credentials and platform guide
        """
        # Send WhatsApp
        try:
            result = await WhatsAppService.send_template_message(
                to_mobile=mobile,
                content_sid=TEMPLATE_WELCOME["sid"],
                content_variables=get_welcome_variables(client_name)
            )
            if result.success:
                logger.info(f"Welcome WhatsApp sent to client {mobile}")
            else:
                logger.warning(f"WhatsApp failed for client {mobile}: {result.error}")
        except Exception as e:
            logger.error(f"WhatsApp error for client {mobile}: {e}")
        
        # Send Email if available
        if email:
            try:
                template_data = {
                    "client_name": client_name,
                    "username": username,
                    "mobile": mobile,
                    "password": password,
                    "therapist_name": therapist_name,
                    "login_url": login_url,
                }
                email_content = get_email_template("client_welcome", template_data)
                message = EmailMessage(
                    to=email,
                    subject=email_content["subject"],
                    html_body=email_content["html_body"],
                    text_body=email_content["text_body"]
                )
                result = await EmailProviderRegistry.send_email(message)
                if result.success:
                    logger.info(f"Welcome email sent to client {email}")
                else:
                    logger.warning(f"Email failed for client {email}: {result.error}")
            except Exception as e:
                logger.error(f"Email error for client {email}: {e}")
    
    @staticmethod
    async def send_appointment_confirmation(
        client_name: str,
        client_mobile: str,
        client_email: Optional[str],
        therapist_name: str,
        appointment_datetime: str,
        duration: int = 50,
        dashboard_url: str = "https://cognispace.in/login"
    ):
        """
        Send appointment confirmation to client.
        - WhatsApp: Appointment confirmed message (template cogni_appointment)
        - Email: Appointment confirmation with details
        """
        date_str = format_date_ist(appointment_datetime)
        time_str = format_time_ist(appointment_datetime)
        
        # Send WhatsApp
        try:
            result = await WhatsAppService.send_template_message(
                to_mobile=client_mobile,
                content_sid=TEMPLATE_APPOINTMENT_CONFIRMED["sid"],
                content_variables=get_appointment_confirmed_variables(
                    client_name=client_name,
                    therapist_name=therapist_name,
                    date=date_str,
                    time=time_str
                )
            )
            if result.success:
                logger.info(f"Appointment WhatsApp sent to {client_mobile}")
            else:
                logger.warning(f"WhatsApp failed for {client_mobile}: {result.error}")
        except Exception as e:
            logger.error(f"WhatsApp error for {client_mobile}: {e}")
        
        # Send Email
        if client_email:
            try:
                template_data = {
                    "appointment_time": appointment_datetime,
                    "therapist_name": therapist_name,
                    "client_name": client_name,
                    "duration": duration,
                    "dashboard_url": dashboard_url,
                }
                email_content = get_email_template("appointment_confirmation", template_data)
                message = EmailMessage(
                    to=client_email,
                    subject=email_content["subject"],
                    html_body=email_content["html_body"],
                    text_body=email_content["text_body"],
                    from_name=therapist_name  # Sender name = Therapist name
                )
                result = await EmailProviderRegistry.send_email(message)
                if result.success:
                    logger.info(f"Appointment email sent to {client_email}")
                else:
                    logger.warning(f"Email failed for {client_email}: {result.error}")
            except Exception as e:
                logger.error(f"Email error for {client_email}: {e}")
    
    @staticmethod
    async def send_appointment_reminder(
        client_name: str,
        client_mobile: str,
        client_email: Optional[str],
        therapist_name: str,
        appointment_datetime: str
    ):
        """
        Send appointment reminder to client (1 hour before).
        - WhatsApp: Gentle reminder message (template cogni_rem)
        - Email: Reminder with details
        """
        date_str = format_date_ist(appointment_datetime)
        time_str = format_time_ist(appointment_datetime)
        
        # Send WhatsApp
        try:
            result = await WhatsAppService.send_template_message(
                to_mobile=client_mobile,
                content_sid=TEMPLATE_APPOINTMENT_REMINDER["sid"],
                content_variables=get_appointment_reminder_variables(
                    client_name=client_name,
                    therapist_name=therapist_name,
                    date=date_str,
                    time=time_str
                )
            )
            if result.success:
                logger.info(f"Reminder WhatsApp sent to {client_mobile}")
            else:
                logger.warning(f"WhatsApp failed for {client_mobile}: {result.error}")
        except Exception as e:
            logger.error(f"WhatsApp error for {client_mobile}: {e}")
        
        # Send Email
        if client_email:
            try:
                template_data = {
                    "appointment_time": appointment_datetime,
                    "therapist_name": therapist_name,
                    "client_name": client_name,
                    "time_until": "1 hour",
                }
                email_content = get_email_template("appointment_reminder", template_data)
                message = EmailMessage(
                    to=client_email,
                    subject=email_content["subject"],
                    html_body=email_content["html_body"],
                    text_body=email_content["text_body"],
                    from_name=therapist_name  # Sender name = Therapist name
                )
                result = await EmailProviderRegistry.send_email(message)
                if result.success:
                    logger.info(f"Reminder email sent to {client_email}")
                else:
                    logger.warning(f"Email failed for {client_email}: {result.error}")
            except Exception as e:
                logger.error(f"Email error for {client_email}: {e}")
    
    @staticmethod
    async def send_payment_received(
        client_name: str,
        client_mobile: str,
        client_email: Optional[str],
        therapist_name: str,
        amount: float,
        payment_date: str,
        receipt_number: Optional[str] = None,
        payment_method: str = "Cash"
    ):
        """
        Send payment received notification to client.
        - WhatsApp: Payment confirmation (template cogni_pay)
        - Email: Payment receipt with details
        """
        date_str = format_date_ist(payment_date)
        amount_str = f"{amount:,.0f}"
        
        # Send WhatsApp
        try:
            result = await WhatsAppService.send_template_message(
                to_mobile=client_mobile,
                content_sid=TEMPLATE_PAYMENT_RECEIVED["sid"],
                content_variables=get_payment_received_variables(
                    client_name=client_name,
                    amount=amount_str,
                    therapist_name=therapist_name,
                    date=date_str
                )
            )
            if result.success:
                logger.info(f"Payment WhatsApp sent to {client_mobile}")
            else:
                logger.warning(f"WhatsApp failed for {client_mobile}: {result.error}")
        except Exception as e:
            logger.error(f"WhatsApp error for {client_mobile}: {e}")
        
        # Send Email
        if client_email:
            try:
                template_data = {
                    "amount": amount,
                    "payment_date": payment_date,
                    "receipt_number": receipt_number or "N/A",
                    "payment_method": payment_method,
                    "therapist_name": therapist_name,
                    "client_name": client_name,
                }
                email_content = get_email_template("payment_receipt", template_data)
                message = EmailMessage(
                    to=client_email,
                    subject=email_content["subject"],
                    html_body=email_content["html_body"],
                    text_body=email_content["text_body"],
                    from_name=therapist_name  # Sender name = Therapist name
                )
                result = await EmailProviderRegistry.send_email(message)
                if result.success:
                    logger.info(f"Payment email sent to {client_email}")
                else:
                    logger.warning(f"Email failed for {client_email}: {result.error}")
            except Exception as e:
                logger.error(f"Email error for {client_email}: {e}")


    @staticmethod
    async def send_appointment_cancellation(
        client_name: str,
        client_email: Optional[str],
        therapist_name: str,
        therapist_email: Optional[str],
        assistant_email: Optional[str],
        appointment_datetime: str,
        cancelled_by: str,
        cancellation_reason: str = ""
    ):
        """
        Send appointment cancellation notification to client, therapist, and assistant.
        Only via email.
        """
        template_data = {
            "client_name": client_name,
            "therapist_name": therapist_name,
            "appointment_time": appointment_datetime,
            "cancelled_by": cancelled_by,
            "cancellation_reason": cancellation_reason or "No reason provided"
        }
        email_content = get_email_template("appointment_cancellation", template_data)
        
        # Send to all recipients
        recipients = []
        if client_email:
            recipients.append(("client", client_email))
        if therapist_email:
            recipients.append(("therapist", therapist_email))
        if assistant_email:
            recipients.append(("assistant", assistant_email))
        
        for role, email in recipients:
            try:
                message = EmailMessage(
                    to=email,
                    subject=email_content["subject"],
                    html_body=email_content["html_body"],
                    text_body=email_content["text_body"]
                )
                result = await EmailProviderRegistry.send_email(message)
                if result.success:
                    logger.info(f"Cancellation email sent to {role}: {email}")
                else:
                    logger.warning(f"Email failed for {role} {email}: {result.error}")
            except Exception as e:
                logger.error(f"Email error for {role} {email}: {e}")

    @staticmethod
    async def send_client_self_registration_notification(
        client_name: str,
        client_mobile: str,
        client_email: Optional[str],
        therapist_email: Optional[str],
        assistant_email: Optional[str],
        registration_time: str,
        dashboard_url: str = "https://cognispace.in/login"
    ):
        """
        Notify therapist and assistant when a client self-registers.
        Only via email.
        """
        template_data = {
            "client_name": client_name,
            "client_mobile": client_mobile,
            "client_email": client_email or "Not provided",
            "registration_time": registration_time,
            "dashboard_url": dashboard_url
        }
        email_content = get_email_template("client_self_registration", template_data)
        
        recipients = []
        if therapist_email:
            recipients.append(("therapist", therapist_email))
        if assistant_email:
            recipients.append(("assistant", assistant_email))
        
        for role, email in recipients:
            try:
                message = EmailMessage(
                    to=email,
                    subject=email_content["subject"],
                    html_body=email_content["html_body"],
                    text_body=email_content["text_body"]
                )
                result = await EmailProviderRegistry.send_email(message)
                if result.success:
                    logger.info(f"Client registration email sent to {role}: {email}")
                else:
                    logger.warning(f"Email failed for {role} {email}: {result.error}")
            except Exception as e:
                logger.error(f"Email error for {role} {email}: {e}")

    @staticmethod
    async def send_payment_notification_to_therapist(
        client_name: str,
        amount: float,
        payment_method: str,
        receipt_number: str,
        payment_date: str,
        therapist_email: Optional[str],
        assistant_email: Optional[str],
        dashboard_url: str = "https://cognispace.in/login"
    ):
        """
        Notify therapist and assistant when payment is received.
        Only via email.
        """
        template_data = {
            "client_name": client_name,
            "amount": amount,
            "payment_method": payment_method,
            "receipt_number": receipt_number,
            "payment_date": payment_date,
            "dashboard_url": dashboard_url
        }
        email_content = get_email_template("payment_received_therapist", template_data)
        
        recipients = []
        if therapist_email:
            recipients.append(("therapist", therapist_email))
        if assistant_email:
            recipients.append(("assistant", assistant_email))
        
        for role, email in recipients:
            try:
                message = EmailMessage(
                    to=email,
                    subject=email_content["subject"],
                    html_body=email_content["html_body"],
                    text_body=email_content["text_body"]
                )
                result = await EmailProviderRegistry.send_email(message)
                if result.success:
                    logger.info(f"Payment notification email sent to {role}: {email}")
                else:
                    logger.warning(f"Email failed for {role} {email}: {result.error}")
            except Exception as e:
                logger.error(f"Email error for {role} {email}: {e}")

    @staticmethod
    async def send_consent_accepted_notification(
        client_name: str,
        therapist_name: str,
        signature_date: str,
        signature_method: str,
        therapist_email: Optional[str],
        assistant_email: Optional[str],
        dashboard_url: str = "https://cognispace.in/login"
    ):
        """
        Notify therapist and assistant when client accepts consent form.
        Only via email.
        """
        template_data = {
            "client_name": client_name,
            "therapist_name": therapist_name,
            "signature_date": signature_date,
            "signature_method": signature_method,
            "consent_summary": "Informed Consent for Psychological Services",
            "dashboard_url": dashboard_url
        }
        email_content = get_email_template("consent_accepted", template_data)
        
        recipients = []
        if therapist_email:
            recipients.append(("therapist", therapist_email))
        if assistant_email:
            recipients.append(("assistant", assistant_email))
        
        for role, email in recipients:
            try:
                message = EmailMessage(
                    to=email,
                    subject=email_content["subject"],
                    html_body=email_content["html_body"],
                    text_body=email_content["text_body"]
                )
                result = await EmailProviderRegistry.send_email(message)
                if result.success:
                    logger.info(f"Consent accepted email sent to {role}: {email}")
                else:
                    logger.warning(f"Email failed for {role} {email}: {result.error}")
            except Exception as e:
                logger.error(f"Email error for {role} {email}: {e}")

    @staticmethod
    async def send_daily_summary(
        recipient_email: str,
        recipient_name: str,
        date: str,
        appointments: list,
        pending_payments: list,
        pending_notes: list,
        is_assistant: bool = False,
        dashboard_url: str = "https://cognispace.in/login"
    ):
        """
        Send daily summary email to therapist or assistant.
        Includes: today's appointments, pending payments, pending session notes
        """
        template_data = {
            "date": date,
            "appointments": appointments,
            "pending_payments": pending_payments,
            "pending_notes": pending_notes,
            "is_assistant": is_assistant,
            "dashboard_url": dashboard_url
        }
        email_content = get_email_template("daily_summary", template_data)
        
        try:
            message = EmailMessage(
                to=recipient_email,
                subject=email_content["subject"],
                html_body=email_content["html_body"],
                text_body=email_content["text_body"]
            )
            result = await EmailProviderRegistry.send_email(message)
            if result.success:
                logger.info(f"Daily summary email sent to {recipient_email}")
            else:
                logger.warning(f"Daily summary email failed for {recipient_email}: {result.error}")
        except Exception as e:
            logger.error(f"Daily summary email error for {recipient_email}: {e}")
