"""
Resend Email Provider Implementation
"""
import os
from typing import List, Dict, Any
from .base import EmailProviderBase, EmailMessage, EmailResult


class ResendProvider(EmailProviderBase):
    """
    Resend email provider implementation.
    Uses Resend API for sending emails.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key') or os.environ.get('RESEND_API_KEY')
        self.resend_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Resend client if API key is available"""
        if self.api_key:
            try:
                import resend
                resend.api_key = self.api_key
                self.resend_client = resend
            except ImportError:
                print("Resend library not installed. Run: pip install resend")
                self.resend_client = None
    
    def validate_config(self) -> bool:
        """Validate Resend configuration"""
        return bool(self.api_key)
    
    @property
    def is_available(self) -> bool:
        """Check if Resend is available"""
        return self.resend_client is not None and bool(self.api_key)
    
    async def send(self, message: EmailMessage) -> EmailResult:
        """Send email via Resend"""
        if not self.is_available:
            return EmailResult(
                success=False,
                provider="resend",
                error="Resend provider not configured or unavailable"
            )
        
        try:
            default_email, default_name = self.get_default_sender()
            from_email = message.from_email or default_email
            from_name = message.from_name or default_name
            
            params = {
                "from": f"{from_name} <{from_email}>",
                "to": [message.to],
                "subject": message.subject,
                "html": message.html_body,
            }
            
            if message.text_body:
                params["text"] = message.text_body
            
            if message.reply_to:
                params["reply_to"] = message.reply_to
            
            if message.cc:
                params["cc"] = message.cc
            
            if message.bcc:
                params["bcc"] = message.bcc
            
            # Send via Resend
            response = self.resend_client.Emails.send(params)
            
            return EmailResult(
                success=True,
                provider="resend",
                message_id=response.get("id") if isinstance(response, dict) else str(response)
            )
            
        except Exception as e:
            return EmailResult(
                success=False,
                provider="resend",
                error=str(e)
            )
    
    async def send_bulk(self, messages: List[EmailMessage]) -> List[EmailResult]:
        """Send multiple emails via Resend"""
        results = []
        for message in messages:
            result = await self.send(message)
            results.append(result)
        return results
