"""
Twilio WhatsApp Provider - Send WhatsApp messages via Twilio API
"""
import os
import asyncio
import logging
from typing import Dict, Any, List, Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from .base import WhatsAppProviderBase, WhatsAppMessage, WhatsAppResult

logger = logging.getLogger(__name__)


class TwilioWhatsAppProvider(WhatsAppProviderBase):
    """
    Twilio WhatsApp provider implementation.
    Uses Twilio's WhatsApp Business API for sending template messages.
    
    Required config:
    - account_sid: Twilio Account SID
    - auth_token: Twilio Auth Token  
    - from_number: WhatsApp-enabled Twilio number (e.g., whatsapp:+14155238886)
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.provider_name = "twilio"
        
        # Get credentials from config or environment
        self.account_sid = config.get('account_sid') or os.environ.get('TWILIO_ACCOUNT_SID')
        self.auth_token = config.get('auth_token') or os.environ.get('TWILIO_AUTH_TOKEN')
        self.from_number = config.get('from_number') or os.environ.get('TWILIO_WHATSAPP_FROM')
        
        # Initialize Twilio client if credentials available
        self._client = None
        if self.account_sid and self.auth_token:
            try:
                self._client = Client(self.account_sid, self.auth_token)
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
    
    def validate_config(self) -> bool:
        """Validate Twilio configuration"""
        if not self.account_sid:
            logger.warning("Twilio Account SID not configured")
            return False
        if not self.auth_token:
            logger.warning("Twilio Auth Token not configured")
            return False
        if not self.from_number:
            logger.warning("Twilio WhatsApp From number not configured")
            return False
        return True
    
    @property
    def is_available(self) -> bool:
        """Check if Twilio is properly configured"""
        return self._client is not None and self.validate_config()
    
    async def send(self, message: WhatsAppMessage) -> WhatsAppResult:
        """
        Send WhatsApp message via Twilio.
        
        For template messages, Twilio uses Content Templates.
        For simple text (sandbox), we can send plain text.
        """
        if not self.is_available:
            return WhatsAppResult(
                success=False,
                provider=self.provider_name,
                error="Twilio WhatsApp provider not properly configured"
            )
        
        try:
            # Normalize phone number and add WhatsApp prefix
            to_number = self.normalize_phone(message.to)
            if not to_number.startswith("whatsapp:"):
                to_number = f"whatsapp:{to_number}"
            
            from_number = self.from_number
            if not from_number.startswith("whatsapp:"):
                from_number = f"whatsapp:{from_number}"
            
            # Build message body from template params
            # In production, use Content Templates. For now, use plain text.
            body = self._build_message_body(message.template_name, message.template_params or [])
            
            # Send message asynchronously
            twilio_message = await asyncio.to_thread(
                self._send_message,
                from_number=from_number,
                to_number=to_number,
                body=body
            )
            
            return WhatsAppResult(
                success=True,
                provider=self.provider_name,
                message_id=twilio_message.sid
            )
            
        except TwilioRestException as e:
            logger.error(f"Twilio API error: {e.msg}")
            return WhatsAppResult(
                success=False,
                provider=self.provider_name,
                error=f"Twilio error: {e.msg}"
            )
        except Exception as e:
            logger.error(f"Error sending WhatsApp via Twilio: {e}")
            return WhatsAppResult(
                success=False,
                provider=self.provider_name,
                error=str(e)
            )
    
    def _send_message(self, from_number: str, to_number: str, body: str):
        """Synchronous message send (called via asyncio.to_thread)"""
        return self._client.messages.create(
            from_=from_number,
            to=to_number,
            body=body
        )
    
    def _build_message_body(self, template_name: str, params: List[str]) -> str:
        """
        Build message body from template name and parameters.
        
        Templates (no clinical content):
        - appointment_confirmation: params[0]=therapist, params[1]=date, params[2]=time
        - appointment_reminder: params[0]=therapist, params[1]=time_until
        - payment_receipt: params[0]=amount, params[1]=date
        """
        templates = {
            "appointment_confirmation": (
                "✅ *Appointment Confirmed*\n\n"
                "Your session with {0} is scheduled for {1} at {2}.\n\n"
                "Please arrive 5 minutes early.\n\n"
                "_COGNISPACE_"
            ),
            "appointment_reminder": (
                "⏰ *Appointment Reminder*\n\n"
                "Your session with {0} is in {1}.\n\n"
                "See you soon!\n\n"
                "_COGNISPACE_"
            ),
            "payment_receipt": (
                "💳 *Payment Received*\n\n"
                "Amount: ₹{0}\n"
                "Date: {1}\n\n"
                "Thank you for your payment.\n\n"
                "_COGNISPACE_"
            )
        }
        
        template = templates.get(template_name)
        if template and params:
            try:
                return template.format(*params)
            except (IndexError, KeyError):
                logger.warning(f"Template param mismatch for {template_name}")
                return template
        
        return f"COGNISPACE: {template_name}"
    
    async def send_bulk(self, messages: List[WhatsAppMessage]) -> List[WhatsAppResult]:
        """Send multiple WhatsApp messages"""
        results = []
        for message in messages:
            result = await self.send(message)
            results.append(result)
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.1)
        return results
    
    async def get_template_status(self, template_name: str) -> Dict[str, Any]:
        """Get template status (for Twilio Content Templates)"""
        # Twilio Content Templates are managed in console
        # This returns a basic status for our local templates
        local_templates = ["appointment_confirmation", "appointment_reminder", "payment_receipt"]
        
        return {
            "template_name": template_name,
            "exists": template_name in local_templates,
            "status": "approved" if template_name in local_templates else "unknown",
            "provider": self.provider_name
        }
    
    async def send_direct(self, to_mobile: str, message: str) -> WhatsAppResult:
        """
        Send a direct text message via WhatsApp (for account notifications).
        Note: This uses freeform text which only works in Twilio Sandbox.
        For production, use send_template_message instead.
        """
        if not self.is_available:
            return WhatsAppResult(
                success=False,
                provider=self.provider_name,
                error="Twilio WhatsApp provider not properly configured"
            )
        
        try:
            to_number = self.normalize_phone(to_mobile)
            if not to_number.startswith("whatsapp:"):
                to_number = f"whatsapp:{to_number}"
            
            from_number = self.from_number
            if not from_number.startswith("whatsapp:"):
                from_number = f"whatsapp:{from_number}"
            
            twilio_message = await asyncio.to_thread(
                self._send_message,
                from_number=from_number,
                to_number=to_number,
                body=message
            )
            
            return WhatsAppResult(
                success=True,
                provider=self.provider_name,
                message_id=twilio_message.sid
            )
        except TwilioRestException as e:
            logger.error(f"Twilio API error: {e.msg}")
            return WhatsAppResult(
                success=False,
                provider=self.provider_name,
                error=f"Twilio error: {e.msg}"
            )
        except Exception as e:
            logger.error(f"Error sending direct WhatsApp: {e}")
            return WhatsAppResult(
                success=False,
                provider=self.provider_name,
                error=str(e)
            )

    async def send_template_message(
        self, 
        to_mobile: str, 
        content_sid: str, 
        content_variables: dict
    ) -> WhatsAppResult:
        """
        Send WhatsApp message using approved Content Template.
        This is the production-ready method that uses pre-approved templates.
        
        Args:
            to_mobile: Recipient phone number
            content_sid: Twilio Content Template SID (e.g., HXxxxxxxxxx)
            content_variables: Dict of template variables (e.g., {"1": "John Doe"})
        """
        if not self.is_available:
            return WhatsAppResult(
                success=False,
                provider=self.provider_name,
                error="Twilio WhatsApp provider not properly configured"
            )
        
        try:
            to_number = self.normalize_phone(to_mobile)
            if not to_number.startswith("whatsapp:"):
                to_number = f"whatsapp:{to_number}"
            
            from_number = self.from_number
            if not from_number.startswith("whatsapp:"):
                from_number = f"whatsapp:{from_number}"
            
            # Convert content_variables dict to JSON string
            import json
            content_vars_json = json.dumps(content_variables)
            
            # Send using Content Template
            twilio_message = await asyncio.to_thread(
                self._send_template_message,
                from_number=from_number,
                to_number=to_number,
                content_sid=content_sid,
                content_variables=content_vars_json
            )
            
            return WhatsAppResult(
                success=True,
                provider=self.provider_name,
                message_id=twilio_message.sid
            )
        except TwilioRestException as e:
            logger.error(f"Twilio Template API error: {e.msg}")
            return WhatsAppResult(
                success=False,
                provider=self.provider_name,
                error=f"Twilio error: {e.msg}"
            )
        except Exception as e:
            logger.error(f"Error sending template WhatsApp: {e}")
            return WhatsAppResult(
                success=False,
                provider=self.provider_name,
                error=str(e)
            )
    
    def _send_template_message(
        self, 
        from_number: str, 
        to_number: str, 
        content_sid: str,
        content_variables: str
    ):
        """Synchronous template message send (called via asyncio.to_thread)"""
        logger.info(f"Sending template message: content_sid={content_sid}, variables={content_variables}")
        logger.info(f"From: {from_number}, To: {to_number}")
        return self._client.messages.create(
            from_=from_number,
            to=to_number,
            content_sid=content_sid,
            content_variables=content_variables
        )
