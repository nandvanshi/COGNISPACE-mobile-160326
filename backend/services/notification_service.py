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
    TEMPLATE_APPOINTMENT_REQUEST,
    TEMPLATE_DAILY_SCHEDULE,
    get_welcome_variables,
    get_appointment_confirmed_variables,
    get_appointment_reminder_variables,
    get_payment_received_variables,
    get_appointment_request_variables,
    get_daily_schedule_variables,
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
        # Check if already has timezone info
        if dt.tzinfo is not None:
            # Convert to IST timezone properly
            ist_tz = timezone(timedelta(hours=5, minutes=30))
            ist_dt = dt.astimezone(ist_tz)
        else:
            # Assume UTC and add IST offset
            ist_dt = dt + timedelta(hours=5, minutes=30)
        return ist_dt.strftime("%d/%m/%Y")
    except Exception:
        # If parsing fails, try to extract date from string
        if len(dt_str) >= 10:
            try:
                # Try DD/MM/YYYY format
                return dt_str[:10]
            except Exception:
                pass
        return dt_str


def format_time_ist(dt_str: str) -> str:
    """Format datetime string to IST time (HH:MM AM/PM)"""
    if not dt_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        # Check if already has timezone info
        if dt.tzinfo is not None:
            # Convert to IST timezone properly
            ist_tz = timezone(timedelta(hours=5, minutes=30))
            ist_dt = dt.astimezone(ist_tz)
        else:
            # Assume UTC and add IST offset
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
        client_email: Optional[str] = None,
        dashboard_url: str = "https://cognispace.in/login"
    ):
        """
        Notify therapist, assistant, and client when consent form is signed.
        """
        template_data = {
            "client_name": client_name,
            "therapist_name": therapist_name,
            "signature_date": signature_date,
            "signature_method": signature_method,
            "consent_summary": "Informed Consent for Psychological Services",
            "dashboard_url": dashboard_url
        }
        
        # Send to therapist and assistant
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
        
        # Send confirmation to client
        if client_email:
            try:
                client_email_content = get_email_template("consent_confirmation_client", template_data)
                message = EmailMessage(
                    to=client_email,
                    subject=client_email_content["subject"],
                    html_body=client_email_content["html_body"],
                    text_body=client_email_content["text_body"],
                    from_name=therapist_name  # Send from therapist's name
                )
                result = await EmailProviderRegistry.send_email(message)
                if result.success:
                    logger.info(f"Consent confirmation email sent to client: {client_email}")
                else:
                    logger.warning(f"Client email failed for {client_email}: {result.error}")
            except Exception as e:
                logger.error(f"Client email error for {client_email}: {e}")

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



    @staticmethod
    async def send_public_booking_confirmation(
        client_email: str,
        client_name: str,
        therapist_name: str,
        appointment_time: str,
        temp_password: str,
        mobile: str
    ):
        """Send booking confirmation with account credentials to new client"""
        
        # Format appointment time
        appt_date = format_date_ist(appointment_time)
        appt_time_formatted = format_time_ist(appointment_time)
        
        html_body = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #0d5c4d 0%, #1a7a6a 100%); padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">Booking Request Submitted! 🎉</h1>
            </div>
            
            <div style="background: #f8faf9; padding: 30px; border-radius: 0 0 12px 12px; border: 1px solid #e0e0e0; border-top: none;">
                <p style="font-size: 16px; color: #333;">Hello <strong>{client_name}</strong>,</p>
                
                <p style="color: #555;">Your appointment request with <strong>{therapist_name}</strong> has been submitted and is awaiting approval.</p>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #0d5c4d;">
                    <h3 style="margin: 0 0 15px 0; color: #0d5c4d;">📅 Appointment Details</h3>
                    <p style="margin: 5px 0;"><strong>Date:</strong> {appt_date}</p>
                    <p style="margin: 5px 0;"><strong>Time:</strong> {appt_time_formatted}</p>
                    <p style="margin: 5px 0;"><strong>Therapist:</strong> {therapist_name}</p>
                    <p style="margin: 5px 0;"><strong>Status:</strong> <span style="color: #f59e0b;">Awaiting Approval</span></p>
                </div>
                
                <div style="background: #e8f5e9; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin: 0 0 15px 0; color: #2e7d32;">🔐 Your Account Created</h3>
                    <p style="margin: 5px 0;"><strong>Mobile:</strong> {mobile}</p>
                    <p style="margin: 5px 0;"><strong>Temporary Password:</strong> <code style="background: #fff; padding: 2px 8px; border-radius: 4px;">{temp_password}</code></p>
                    <p style="font-size: 13px; color: #666; margin-top: 10px;">Use these credentials to login and track your appointment status.</p>
                </div>
                
                <p style="color: #666; font-size: 14px;">You will receive another email once the therapist approves your appointment.</p>
                
                <div style="text-align: center; margin-top: 25px;">
                    <a href="https://cognispace.in/login" style="background: #0d5c4d; color: white; padding: 12px 30px; border-radius: 25px; text-decoration: none; font-weight: 500;">Login to CogniSpace</a>
                </div>
            </div>
            
            <p style="text-align: center; color: #999; font-size: 12px; margin-top: 20px;">
                © CogniSpace - Your Mental Wellness Partner
            </p>
        </div>
        """
        
        try:
            message = EmailMessage(
                to=client_email,
                subject=f"Booking Request Submitted - {therapist_name}",
                html_body=html_body,
                text_body=f"Hello {client_name}, your booking request with {therapist_name} for {appt_date} at {appt_time_formatted} has been submitted. Your login: Mobile: {mobile}, Password: {temp_password}"
            )
            await EmailProviderRegistry.send_email(message)
            logger.info(f"Public booking confirmation sent to {client_email}")
        except Exception as e:
            logger.error(f"Public booking confirmation error: {e}")

    @staticmethod
    async def send_booking_request_notification(
        client_email: str,
        client_name: str,
        therapist_name: str,
        appointment_time: str
    ):
        """Send booking notification to existing client"""
        appt_date = format_date_ist(appointment_time)
        appt_time_formatted = format_time_ist(appointment_time)
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #0d5c4d;">Booking Request Submitted</h2>
            <p>Hello {client_name},</p>
            <p>Your appointment request with <strong>{therapist_name}</strong> has been submitted.</p>
            <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <p><strong>Date:</strong> {appt_date}</p>
                <p><strong>Time:</strong> {appt_time_formatted}</p>
                <p><strong>Status:</strong> Awaiting Approval</p>
            </div>
            <p>You will be notified once the therapist approves your appointment.</p>
        </div>
        """
        
        try:
            message = EmailMessage(
                to=client_email,
                subject=f"Booking Request Submitted - {therapist_name}",
                html_body=html_body,
                text_body=f"Hello {client_name}, your booking request with {therapist_name} for {appt_date} is awaiting approval."
            )
            await EmailProviderRegistry.send_email(message)
        except Exception as e:
            logger.error(f"Booking notification error: {e}")

    @staticmethod
    async def send_new_booking_request_to_therapist(
        therapist_email: str,
        therapist_name: str,
        client_name: str,
        appointment_time: str
    ):
        """Notify therapist about new booking request"""
        appt_date = format_date_ist(appointment_time)
        appt_time_formatted = format_time_ist(appointment_time)
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #0d5c4d;">🔔 New Booking Request</h2>
            <p>Hello Dr. {therapist_name},</p>
            <p>You have received a new appointment request from <strong>{client_name}</strong>.</p>
            <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #ffc107;">
                <p><strong>Client:</strong> {client_name}</p>
                <p><strong>Requested Date:</strong> {appt_date}</p>
                <p><strong>Requested Time:</strong> {appt_time_formatted}</p>
            </div>
            <p>Please login to CogniSpace to approve or decline this request.</p>
            <div style="text-align: center; margin-top: 20px;">
                <a href="https://cognispace.in/login" style="background: #0d5c4d; color: white; padding: 10px 25px; border-radius: 20px; text-decoration: none;">Review Request</a>
            </div>
        </div>
        """
        
        try:
            message = EmailMessage(
                to=therapist_email,
                subject=f"New Booking Request from {client_name}",
                html_body=html_body,
                text_body=f"New booking request from {client_name} for {appt_date} at {appt_time_formatted}. Login to approve."
            )
            await EmailProviderRegistry.send_email(message)
        except Exception as e:
            logger.error(f"Therapist booking notification error: {e}")


    @staticmethod
    async def send_booking_declined_notification(
        client_email: str,
        client_name: str,
        therapist_name: str,
        appointment_time: str,
        reason: str = ""
    ):
        """Send booking declined notification to client"""
        appt_date = format_date_ist(appointment_time)
        appt_time_formatted = format_time_ist(appointment_time)
        
        reason_text = f"<p><strong>Reason:</strong> {reason}</p>" if reason else ""
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #dc3545;">Booking Request Update</h2>
            <p>Hello {client_name},</p>
            <p>Unfortunately, your appointment request with <strong>{therapist_name}</strong> could not be approved.</p>
            <div style="background: #f8d7da; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #dc3545;">
                <p><strong>Requested Date:</strong> {appt_date}</p>
                <p><strong>Requested Time:</strong> {appt_time_formatted}</p>
                <p><strong>Status:</strong> Declined</p>
                {reason_text}
            </div>
            <p>Please try booking a different time slot or contact the therapist for assistance.</p>
            <div style="text-align: center; margin-top: 20px;">
                <a href="https://cognispace.in/login" style="background: #0d5c4d; color: white; padding: 10px 25px; border-radius: 20px; text-decoration: none;">Book Another Slot</a>
            </div>
        </div>
        """
        
        try:
            message = EmailMessage(
                to=client_email,
                subject=f"Booking Request Update - {therapist_name}",
                html_body=html_body,
                text_body=f"Hello {client_name}, your booking request with {therapist_name} for {appt_date} has been declined. {reason}"
            )
            await EmailProviderRegistry.send_email(message)
            logger.info(f"Booking declined notification sent to {client_email}")
        except Exception as e:
            logger.error(f"Booking declined notification error: {e}")


    @staticmethod
    async def send_appointment_request_whatsapp_to_therapist(
        therapist_mobile: str,
        therapist_name: str,
        client_name: str,
        appointment_datetime: str
    ):
        """
        Send WhatsApp notification to therapist when client requests appointment.
        Template: cogni_t_apreq
        """
        date_str = format_date_ist(appointment_datetime)
        time_str = format_time_ist(appointment_datetime)
        
        try:
            result = await WhatsAppService.send_template_message(
                to_mobile=therapist_mobile,
                content_sid=TEMPLATE_APPOINTMENT_REQUEST["sid"],
                content_variables=get_appointment_request_variables(
                    therapist_name=therapist_name,
                    client_name=client_name,
                    date=date_str,
                    time=time_str
                )
            )
            if result.success:
                logger.info(f"Appointment request WhatsApp sent to therapist {therapist_mobile}")
            else:
                logger.warning(f"WhatsApp failed for therapist {therapist_mobile}: {result.error}")
            return result
        except Exception as e:
            logger.error(f"WhatsApp error for therapist {therapist_mobile}: {e}")
            return None

    @staticmethod
    async def send_daily_schedule_whatsapp(
        therapist_mobile: str,
        therapist_name: str,
        date: str,
        appointments: list
    ):
        """
        Send daily schedule WhatsApp to therapist.
        Template: cogni_t_daysh
        
        Args:
            appointments: List of dicts with 'client_name' and 'time' keys
        """
        # Build schedule block
        if not appointments:
            schedule_block = "No appointments scheduled for today."
        else:
            schedule_lines = []
            for idx, appt in enumerate(appointments, 1):
                client_name = appt.get('client_name', 'Client')
                appt_time = appt.get('time', 'N/A')
                schedule_lines.append(f"{idx}. {client_name} - {appt_time}")
            schedule_block = " | ".join(schedule_lines)
        
        try:
            result = await WhatsAppService.send_template_message(
                to_mobile=therapist_mobile,
                content_sid=TEMPLATE_DAILY_SCHEDULE["sid"],
                content_variables=get_daily_schedule_variables(
                    therapist_name=therapist_name,
                    date=date,
                    schedule_block=schedule_block
                )
            )
            if result.success:
                logger.info(f"Daily schedule WhatsApp sent to therapist {therapist_mobile}")
            else:
                logger.warning(f"WhatsApp failed for therapist {therapist_mobile}: {result.error}")
            return result
        except Exception as e:
            logger.error(f"WhatsApp error for therapist {therapist_mobile}: {e}")
            return None

