"""
Email Service - Main email sending service with business logic
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import os

from .base import EmailMessage, EmailResult
from .registry import EmailProviderRegistry
from .templates import get_email_template


class EmailService:
    """
    Main email service that handles business logic for sending emails.
    Checks subscriptions, preferences, and coordinates with provider registry.
    """
    
    _db = None
    
    @classmethod
    async def initialize(cls, db):
        """Initialize email service with database connection"""
        cls._db = db
        await EmailProviderRegistry.initialize(db)
    
    @classmethod
    async def check_subscription_allows_email(cls, therapist_id: str) -> bool:
        """
        Check if therapist's subscription allows email notifications.
        
        Args:
            therapist_id: Therapist user ID
            
        Returns:
            True if email is allowed, False otherwise
        """
        if not cls._db:
            return False
        
        # Get therapist's subscription
        subscription = await cls._db.therapist_subscriptions.find_one(
            {"therapist_id": therapist_id},
            {"_id": 0}
        )
        
        if not subscription:
            return False
        
        # Check if subscription is active
        end_date = subscription.get("end_date")
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                if end_dt < datetime.now(timezone.utc):
                    return False  # Subscription expired
            except:
                pass
        
        # Check if plan allows email
        plan_id = subscription.get("plan_id")
        if plan_id:
            plan = await cls._db.subscription_plans.find_one(
                {"id": plan_id},
                {"_id": 0, "features": 1}
            )
            if plan:
                features = plan.get("features", {})
                return features.get("email_notifications", True)  # Default to True
        
        return True  # Default allow if no restrictions found
    
    @classmethod
    async def check_therapist_preference(cls, therapist_id: str, event: str, channel: str = "email") -> bool:
        """
        Check if therapist has enabled this notification channel for this event.
        
        Args:
            therapist_id: Therapist user ID
            event: Event key (e.g., 'appointment_confirmation')
            channel: 'email' or 'whatsapp'
            
        Returns:
            True if enabled, False otherwise
        """
        if not cls._db:
            return True  # Default to enabled
        
        preference = await cls._db.notification_preferences.find_one({
            "therapist_id": therapist_id,
            "event_key": event
        }, {"_id": 0})
        
        if not preference:
            return True  # Default to enabled if no preference set
        
        if channel == "email":
            return preference.get("send_email", True)
        elif channel == "whatsapp":
            return preference.get("send_whatsapp", False)
        
        return True
    
    @classmethod
    async def check_user_opted_in(cls, user_id: str, channel: str = "email") -> bool:
        """
        Check if user has opted in for this notification channel.
        
        Args:
            user_id: User ID
            channel: 'email' or 'whatsapp'
            
        Returns:
            True if opted in, False otherwise
        """
        if not cls._db:
            return True
        
        user = await cls._db.users.find_one(
            {"id": user_id},
            {"_id": 0, "notification_opt_in": 1, "email": 1, "mobile": 1}
        )
        
        if not user:
            return False
        
        opt_in = user.get("notification_opt_in", {})
        
        if channel == "email":
            # Must have email and be opted in (default True)
            return bool(user.get("email")) and opt_in.get("email", True)
        elif channel == "whatsapp":
            # Must have mobile and explicitly opted in (default False)
            return bool(user.get("mobile")) and opt_in.get("whatsapp", False)
        
        return True
    
    @classmethod
    async def send_notification_email(
        cls,
        to_user_id: str,
        event: str,
        data: Dict[str, Any],
        therapist_id: Optional[str] = None,
        force: bool = False
    ) -> EmailResult:
        """
        Send a notification email with all business logic checks.
        
        Args:
            to_user_id: Recipient user ID
            event: Event key for template selection
            data: Template data
            therapist_id: Associated therapist (for subscription check)
            force: Skip preference checks (for critical emails)
            
        Returns:
            EmailResult
        """
        if not cls._db:
            return EmailResult(
                success=False,
                provider="none",
                error="Email service not initialized"
            )
        
        # Get recipient user
        user = await cls._db.users.find_one(
            {"id": to_user_id},
            {"_id": 0, "email": 1, "full_name": 1, "role": 1}
        )
        
        if not user or not user.get("email"):
            return EmailResult(
                success=False,
                provider="none",
                error="Recipient has no email address"
            )
        
        # Determine therapist_id if not provided
        if not therapist_id and user.get("role") == "client":
            profile = await cls._db.client_profiles.find_one(
                {"user_id": to_user_id},
                {"_id": 0, "therapist_id": 1}
            )
            if profile:
                therapist_id = profile.get("therapist_id")
        elif not therapist_id and user.get("role") == "therapist":
            therapist_id = to_user_id
        
        if not force:
            # Check subscription allows email
            if therapist_id:
                if not await cls.check_subscription_allows_email(therapist_id):
                    return EmailResult(
                        success=False,
                        provider="none",
                        error="Email notifications not allowed by subscription"
                    )
                
                # Check therapist preference
                if not await cls.check_therapist_preference(therapist_id, event, "email"):
                    return EmailResult(
                        success=False,
                        provider="none",
                        error="Email disabled by therapist for this event"
                    )
            
            # Check user opt-in
            if not await cls.check_user_opted_in(to_user_id, "email"):
                return EmailResult(
                    success=False,
                    provider="none",
                    error="User has not opted in for email notifications"
                )
        
        # Get template
        template = get_email_template(event, data)
        
        # Create email message
        message = EmailMessage(
            to=user["email"],
            subject=template["subject"],
            html_body=template["html_body"],
            text_body=template.get("text_body"),
            metadata={
                "event": event,
                "user_id": to_user_id,
                "therapist_id": therapist_id
            }
        )
        
        # Send via registry (handles provider selection and fallback)
        result = await EmailProviderRegistry.send_email(message)
        
        # Log the attempt
        await cls._log_email_attempt(to_user_id, event, result)
        
        return result
    
    @classmethod
    async def _log_email_attempt(cls, user_id: str, event: str, result: EmailResult):
        """Log email send attempt to database"""
        if not cls._db:
            return
        
        log_entry = {
            "user_id": user_id,
            "event": event,
            "channel": "email",
            "provider": result.provider,
            "success": result.success,
            "message_id": result.message_id,
            "error": result.error,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await cls._db.notification_logs.insert_one(log_entry)
    
    @classmethod
    async def send_welcome_email(cls, user_id: str, login_id: str, password: str, therapist_name: str):
        """Send welcome email with credentials"""
        return await cls.send_notification_email(
            to_user_id=user_id,
            event="welcome_credentials",
            data={
                "login_id": login_id,
                "password": password,
                "therapist_name": therapist_name,
                "login_url": os.environ.get("APP_URL", "https://cognispace.in") + "/login"
            },
            force=True  # Always send welcome emails
        )
    
    @classmethod
    async def send_password_change_email(cls, user_id: str, login_id: str):
        """Send password change notification"""
        return await cls.send_notification_email(
            to_user_id=user_id,
            event="password_changed",
            data={
                "login_id": login_id,
                "changed_at": datetime.now(timezone.utc).isoformat()
            },
            force=True  # Security emails always sent
        )
    
    @classmethod
    async def send_appointment_confirmation_email(
        cls,
        client_id: str,
        therapist_id: str,
        therapist_name: str,
        appointment_time: str,
        duration: int = 50
    ):
        """Send appointment confirmation email"""
        return await cls.send_notification_email(
            to_user_id=client_id,
            event="appointment_confirmation",
            data={
                "therapist_name": therapist_name,
                "appointment_time": appointment_time,
                "duration": duration,
                "dashboard_url": os.environ.get("APP_URL", "https://cognispace.in") + "/login"
            },
            therapist_id=therapist_id
        )
    
    @classmethod
    async def send_payment_receipt_email(
        cls,
        client_id: str,
        therapist_id: str,
        therapist_name: str,
        amount: float,
        payment_date: str,
        receipt_number: str,
        payment_method: str = "Cash"
    ):
        """Send payment receipt email"""
        return await cls.send_notification_email(
            to_user_id=client_id,
            event="payment_receipt",
            data={
                "therapist_name": therapist_name,
                "amount": amount,
                "payment_date": payment_date,
                "receipt_number": receipt_number,
                "payment_method": payment_method,
                "receipt_url": os.environ.get("APP_URL", "https://cognispace.in") + "/login"
            },
            therapist_id=therapist_id
        )
