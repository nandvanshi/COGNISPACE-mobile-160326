"""
WhatsApp Provider Registry - Dynamic provider management
"""
from typing import Dict, Any, Optional, Type
from motor.motor_asyncio import AsyncIOMotorClient
import os
import json

from .base import WhatsAppProviderBase, WhatsAppMessage, WhatsAppResult


# Provider class mapping - Add providers here as they're implemented
PROVIDER_CLASSES: Dict[str, Type[WhatsAppProviderBase]] = {
    # "twilio": TwilioProvider,
    # "gupshup": GupshupProvider,
    # "meta": MetaProvider,
}


class WhatsAppProviderRegistry:
    """
    Dynamic WhatsApp provider registry.
    Loads providers from database and manages provider instances.
    """
    
    _instance = None
    _providers: Dict[str, WhatsAppProviderBase] = {}
    _db = None
    _templates: Dict[str, Dict[str, str]] = {}  # event -> {provider: template_id}
    
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
        await cls._load_templates()
    
    @classmethod
    async def _load_providers(cls):
        """Load active providers from database"""
        if not cls._db:
            return
        
        # Get all active WhatsApp providers
        providers = await cls._db.whatsapp_providers.find(
            {"is_active": True}
        ).sort("priority", 1).to_list(100)
        
        for provider_doc in providers:
            code = provider_doc.get("code")
            if code in PROVIDER_CLASSES:
                try:
                    credentials = provider_doc.get("credentials", {})
                    if isinstance(credentials, str):
                        credentials = json.loads(credentials)
                    
                    provider_class = PROVIDER_CLASSES[code]
                    cls._providers[code] = provider_class(credentials)
                except Exception as e:
                    print(f"Failed to initialize WhatsApp provider {code}: {e}")
    
    @classmethod
    async def _load_templates(cls):
        """Load WhatsApp templates from database"""
        if not cls._db:
            return
        
        templates = await cls._db.whatsapp_templates.find({}).to_list(500)
        
        for t in templates:
            event = t.get("event")
            provider = t.get("provider_code")
            template_id = t.get("template_id")
            
            if event not in cls._templates:
                cls._templates[event] = {}
            
            cls._templates[event][provider] = template_id
    
    @classmethod
    def get_provider(cls, code: str = None) -> Optional[WhatsAppProviderBase]:
        """Get a specific provider or the default provider"""
        if code:
            return cls._providers.get(code)
        
        # Return first available provider
        for provider in cls._providers.values():
            if provider.is_available:
                return provider
        
        return None
    
    @classmethod
    def get_template_id(cls, event: str, provider_code: str) -> Optional[str]:
        """Get template ID for an event and provider"""
        if event in cls._templates:
            return cls._templates[event].get(provider_code)
        return None
    
    @classmethod
    async def add_provider(cls, code: str, name: str, credentials: Dict[str, Any], priority: int = 10):
        """Add a new provider to the registry"""
        if code not in PROVIDER_CLASSES:
            raise ValueError(f"Unknown provider code: {code}. Available: {list(PROVIDER_CLASSES.keys())}")
        
        if cls._db:
            await cls._db.whatsapp_providers.update_one(
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
        
        provider_class = PROVIDER_CLASSES[code]
        cls._providers[code] = provider_class(credentials)
    
    @classmethod
    async def add_template(cls, event: str, provider_code: str, template_id: str, language: str = "en"):
        """Add a template mapping"""
        if cls._db:
            await cls._db.whatsapp_templates.update_one(
                {"event": event, "provider_code": provider_code},
                {"$set": {
                    "event": event,
                    "provider_code": provider_code,
                    "template_id": template_id,
                    "language": language
                }},
                upsert=True
            )
        
        if event not in cls._templates:
            cls._templates[event] = {}
        cls._templates[event][provider_code] = template_id
    
    @classmethod
    async def send_message(cls, message: WhatsAppMessage, provider_code: str = None) -> WhatsAppResult:
        """
        Send WhatsApp message using the specified or default provider.
        
        Args:
            message: WhatsAppMessage to send
            provider_code: Specific provider to use (optional)
            
        Returns:
            WhatsAppResult
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
        
        return WhatsAppResult(
            success=False,
            provider="none",
            error="No available WhatsApp provider configured"
        )
    
    @classmethod
    def is_configured(cls) -> bool:
        """Check if any WhatsApp provider is configured"""
        return len(cls._providers) > 0 and any(p.is_available for p in cls._providers.values())
