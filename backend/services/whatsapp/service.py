"""
WhatsApp Service - Main WhatsApp messaging service with business logic
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from .base import WhatsAppMessage, WhatsAppResult
from .registry import WhatsAppProviderRegistry


class WhatsAppService:
    """
    Main WhatsApp service that handles business logic for sending messages.
    Checks subscriptions, preferences, opt-in, and coordinates with provider registry.
    """
    
    _db = None
    
    @classmethod
    async def initialize(cls, db):
        """Initialize WhatsApp service with database connection"""
        cls._db = db
        await WhatsAppProviderRegistry.initialize(db)
    
    @classmethod
    async def check_subscription_allows_whatsapp(cls, therapist_id: str) -> bool:
        """Check if therapist's subscription allows WhatsApp notifications"""
        if not cls._db:
            return False
        
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
                    return False
            except:
                pass
        
        # Check if plan allows WhatsApp
        plan_id = subscription.get("plan_id")
        if plan_id:
            plan = await cls._db.subscription_plans.find_one(
                {"id": plan_id},
                {"_id": 0, "features": 1}
            )
            if plan:
                features = plan.get("features", {})
                return features.get("whatsapp_notifications", False)  # Default to False
        
        return False
    
    @classmethod
    async def check_user_whatsapp_opt_in(cls, user_id: str) -> bool:
        """Check if user has opted in for WhatsApp notifications (MANDATORY)"""
        if not cls._db:
            return False
        
        user = await cls._db.users.find_one(
            {"id": user_id},
            {"_id": 0, "mobile": 1, "notification_opt_in": 1}
        )
        
        if not user or not user.get("mobile"):
            return False
        
        opt_in = user.get("notification_opt_in", {})
        # WhatsApp requires EXPLICIT opt-in (default False)
        return opt_in.get("whatsapp", False)
    
    @classmethod
    async def send_notification(
        cls,
        to_user_id: str,
        event: str,
        template_params: list,
        therapist_id: Optional[str] = None
    ) -> WhatsAppResult:
        """
        Send a WhatsApp notification with all business logic checks.
        
        Args:
            to_user_id: Recipient user ID
            event: Event key for template selection
            template_params: List of template parameters
            therapist_id: Associated therapist (for subscription check)
            
        Returns:
            WhatsAppResult
        """
        if not cls._db:
            return WhatsAppResult(
                success=False,
                provider="none",
                error="WhatsApp service not initialized"
            )
        
        # Check if any provider is configured
        if not WhatsAppProviderRegistry.is_configured():
            return WhatsAppResult(
                success=False,
                provider="none",
                error="No WhatsApp provider configured"
            )
        
        # Get recipient user
        user = await cls._db.users.find_one(
            {"id": to_user_id},
            {"_id": 0, "mobile": 1, "full_name": 1, "role": 1}
        )
        
        if not user or not user.get("mobile"):
            return WhatsAppResult(
                success=False,
                provider="none",
                error="Recipient has no mobile number"
            )
        
        # Determine therapist_id if not provided
        if not therapist_id and user.get("role") == "client":
            profile = await cls._db.client_profiles.find_one(
                {"user_id": to_user_id},
                {"_id": 0, "therapist_id": 1}
            )
            if profile:
                therapist_id = profile.get("therapist_id")
        
        # Check subscription allows WhatsApp
        if therapist_id:
            if not await cls.check_subscription_allows_whatsapp(therapist_id):
                return WhatsAppResult(
                    success=False,
                    provider="none",
                    error="WhatsApp notifications not allowed by subscription"
                )
        
        # Check user opt-in (MANDATORY for WhatsApp)
        if not await cls.check_user_whatsapp_opt_in(to_user_id):
            return WhatsAppResult(
                success=False,
                provider="none",
                error="User has not opted in for WhatsApp notifications"
            )
        
        # Get default provider and template
        provider = WhatsAppProviderRegistry.get_provider()
        if not provider:
            return WhatsAppResult(
                success=False,
                provider="none",
                error="No available WhatsApp provider"
            )
        
        template_id = WhatsAppProviderRegistry.get_template_id(event, provider.provider_name.lower())
        if not template_id:
            return WhatsAppResult(
                success=False,
                provider="none",
                error=f"No template configured for event: {event}"
            )
        
        # Create message
        message = WhatsAppMessage(
            to=user["mobile"],
            template_name=template_id,
            template_params=template_params,
            metadata={
                "event": event,
                "user_id": to_user_id,
                "therapist_id": therapist_id
            }
        )
        
        # Send via registry
        result = await WhatsAppProviderRegistry.send_message(message)
        
        # Log the attempt
        await cls._log_whatsapp_attempt(to_user_id, event, result)
        
        return result
    
    @classmethod
    async def _log_whatsapp_attempt(cls, user_id: str, event: str, result: WhatsAppResult):
        """Log WhatsApp send attempt to database"""
        if not cls._db:
            return
        
        log_entry = {
            "user_id": user_id,
            "event": event,
            "channel": "whatsapp",
            "provider": result.provider,
            "success": result.success,
            "message_id": result.message_id,
            "error": result.error,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await cls._db.notification_logs.insert_one(log_entry)
