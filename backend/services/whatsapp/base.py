"""
WhatsApp Provider Base Class - Abstract interface for all WhatsApp providers
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class WhatsAppMessage(BaseModel):
    """Standard WhatsApp message structure"""
    to: str  # Recipient phone number (with country code)
    template_name: str  # Template name registered with provider
    template_params: Optional[List[str]] = None  # Template parameters
    language: str = "en"
    metadata: Optional[Dict[str, Any]] = None


class WhatsAppResult(BaseModel):
    """Standard WhatsApp send result"""
    success: bool
    provider: str
    message_id: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = None
    
    def __init__(self, **data):
        if 'timestamp' not in data or data['timestamp'] is None:
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)


class WhatsAppProviderBase(ABC):
    """
    Abstract base class for WhatsApp providers.
    All WhatsApp providers (Twilio, Gupshup, Meta, etc.) must implement this interface.
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
    async def send(self, message: WhatsAppMessage) -> WhatsAppResult:
        """
        Send a WhatsApp message using a template.
        
        Args:
            message: WhatsAppMessage object with all message details
            
        Returns:
            WhatsAppResult with success status and details
        """
        pass
    
    @abstractmethod
    async def send_bulk(self, messages: List[WhatsAppMessage]) -> List[WhatsAppResult]:
        """
        Send multiple WhatsApp messages (batch sending).
        
        Args:
            messages: List of WhatsAppMessage objects
            
        Returns:
            List of WhatsAppResult objects
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
            True if provider can send messages, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_template_status(self, template_name: str) -> Dict[str, Any]:
        """
        Get status of a WhatsApp template.
        
        Args:
            template_name: Name of the template
            
        Returns:
            Dict with template status info
        """
        pass
    
    def normalize_phone(self, phone: str) -> str:
        """
        Normalize phone number to international format.
        
        Args:
            phone: Phone number (may or may not have country code)
            
        Returns:
            Phone number with country code (e.g., +919876543210)
        """
        phone = phone.strip().replace(" ", "").replace("-", "")
        
        if phone.startswith("+"):
            return phone
        
        # Assume Indian number if no country code
        if len(phone) == 10:
            return f"+91{phone}"
        
        if phone.startswith("91") and len(phone) == 12:
            return f"+{phone}"
        
        return f"+{phone}"
