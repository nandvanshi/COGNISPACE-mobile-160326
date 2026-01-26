"""
Email Provider Registry - Dynamic provider management
"""
from typing import Dict, Any, Optional, Type
from motor.motor_asyncio import AsyncIOMotorClient
import os
import json

from .base import EmailProviderBase, EmailMessage, EmailResult
from .resend_provider import ResendProvider


# Provider class mapping
PROVIDER_CLASSES: Dict[str, Type[EmailProviderBase]] = {
    "resend": ResendProvider,
    # Future providers:
    # "sendgrid": SendGridProvider,
    # "smtp": SMTPProvider,
    # "ses": AmazonSESProvider,
}


class EmailProviderRegistry:
    """
    Dynamic email provider registry.
    Loads providers from database and manages provider instances.
    """
    
    _instance = None
    _providers: Dict[str, EmailProviderBase] = {}
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    async def initialize(cls, db=None):
        """Initialize registry with database connection"""
        if db:
            cls._db = db
        else:
            mongo_url = os.environ.get('MONGO_URL')
            client = AsyncIOMotorClient(mongo_url)
            cls._db = client[os.environ.get('DB_NAME', 'cognispace')]
        
        await cls._load_providers()
    
    @classmethod
    async def _load_providers(cls):
        """Load active providers from database"""
        if not cls._db:
            return
        
        # Get all active email providers
        providers = await cls._db.email_providers.find(
            {"is_active": True}
        ).sort("priority", 1).to_list(100)
        
        for provider_doc in providers:
            code = provider_doc.get("code")
            if code in PROVIDER_CLASSES:
                try:
                    # Decrypt credentials if needed (for now, stored as JSON)
                    credentials = provider_doc.get("credentials", {})
                    if isinstance(credentials, str):
                        credentials = json.loads(credentials)
                    
                    # Create provider instance
                    provider_class = PROVIDER_CLASSES[code]
                    cls._providers[code] = provider_class(credentials)
                except Exception as e:
                    print(f"Failed to initialize email provider {code}: {e}")
        
        # If no providers loaded from DB, initialize default Resend
        if not cls._providers:
            await cls._initialize_default_provider()
    
    @classmethod
    async def _initialize_default_provider(cls):
        """Initialize default Resend provider from environment"""
        api_key = os.environ.get('RESEND_API_KEY')
        if api_key:
            cls._providers["resend"] = ResendProvider({
                "api_key": api_key,
                "default_from_email": "noreply@cognispace.in",
                "default_from_name": "COGNISPACE"
            })
            
            # Also save to database for future reference
            if cls._db:
                await cls._db.email_providers.update_one(
                    {"code": "resend"},
                    {"$set": {
                        "code": "resend",
                        "name": "Resend",
                        "is_active": True,
                        "priority": 1,
                        "credentials": {"api_key": api_key}
                    }},
                    upsert=True
                )
    
    @classmethod
    def get_provider(cls, code: str = None) -> Optional[EmailProviderBase]:
        """
        Get a specific provider or the default (highest priority) provider.
        
        Args:
            code: Provider code (e.g., 'resend', 'sendgrid'). If None, returns default.
            
        Returns:
            EmailProviderBase instance or None
        """
        if code:
            return cls._providers.get(code)
        
        # Return first available provider (sorted by priority)
        for provider in cls._providers.values():
            if provider.is_available:
                return provider
        
        return None
    
    @classmethod
    def get_all_providers(cls) -> Dict[str, EmailProviderBase]:
        """Get all registered providers"""
        return cls._providers.copy()
    
    @classmethod
    async def add_provider(cls, code: str, name: str, credentials: Dict[str, Any], priority: int = 10):
        """
        Add a new provider to the registry (persists to database).
        
        Args:
            code: Provider code (must be in PROVIDER_CLASSES)
            name: Display name
            credentials: Provider credentials
            priority: Priority (lower = higher priority)
        """
        if code not in PROVIDER_CLASSES:
            raise ValueError(f"Unknown provider code: {code}")
        
        # Save to database
        if cls._db:
            await cls._db.email_providers.update_one(
                {"code": code},
                {"$set": {
                    "code": code,
                    "name": name,
                    "is_active": True,
                    "priority": priority,
                    "credentials": credentials
                }},
                upsert=True
            )
        
        # Initialize provider instance
        provider_class = PROVIDER_CLASSES[code]
        cls._providers[code] = provider_class(credentials)
    
    @classmethod
    async def remove_provider(cls, code: str):
        """Remove a provider from the registry"""
        if code in cls._providers:
            del cls._providers[code]
        
        if cls._db:
            await cls._db.email_providers.update_one(
                {"code": code},
                {"$set": {"is_active": False}}
            )
    
    @classmethod
    async def send_email(cls, message: EmailMessage, provider_code: str = None) -> EmailResult:
        """
        Send email using the specified or default provider.
        Includes automatic fallback to next provider on failure.
        
        Args:
            message: EmailMessage to send
            provider_code: Specific provider to use (optional)
            
        Returns:
            EmailResult
        """
        # Try specified provider first
        if provider_code:
            provider = cls.get_provider(provider_code)
            if provider and provider.is_available:
                result = await provider.send(message)
                if result.success:
                    return result
        
        # Fallback through all available providers
        for code, provider in cls._providers.items():
            if provider.is_available:
                result = await provider.send(message)
                if result.success:
                    return result
        
        return EmailResult(
            success=False,
            provider="none",
            error="No available email provider"
        )
