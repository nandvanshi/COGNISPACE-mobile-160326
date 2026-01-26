"""
Email Provider Base Class - Abstract interface for all email providers
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class EmailMessage(BaseModel):
    """Standard email message structure"""
    to: str  # Recipient email
    subject: str
    html_body: str
    text_body: Optional[str] = None
    from_email: Optional[str] = None  # Override default sender
    from_name: Optional[str] = None
    reply_to: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None  # Provider-specific metadata


class EmailResult(BaseModel):
    """Standard email send result"""
    success: bool
    provider: str
    message_id: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = None
    
    def __init__(self, **data):
        if 'timestamp' not in data or data['timestamp'] is None:
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)


class EmailProviderBase(ABC):
    """
    Abstract base class for email providers.
    All email providers (Resend, SendGrid, SMTP, etc.) must implement this interface.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize provider with configuration.
        
        Args:
            config: Provider-specific configuration (API keys, endpoints, etc.)
        """
        self.config = config
        self.provider_name = self.__class__.__name__
    
    @abstractmethod
    async def send(self, message: EmailMessage) -> EmailResult:
        """
        Send an email message.
        
        Args:
            message: EmailMessage object with all email details
            
        Returns:
            EmailResult with success status and details
        """
        pass
    
    @abstractmethod
    async def send_bulk(self, messages: List[EmailMessage]) -> List[EmailResult]:
        """
        Send multiple emails (batch sending).
        
        Args:
            messages: List of EmailMessage objects
            
        Returns:
            List of EmailResult objects
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate provider configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if provider is available and properly configured.
        
        Returns:
            True if provider can send emails, False otherwise
        """
        pass
    
    def get_default_sender(self) -> tuple:
        """
        Get default sender email and name from config.
        
        Returns:
            Tuple of (email, name)
        """
        return (
            self.config.get('default_from_email', 'noreply@cognispace.in'),
            self.config.get('default_from_name', 'COGNISPACE')
        )
