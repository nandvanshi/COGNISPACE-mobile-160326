"""
Email Service Package
"""
from .base import EmailProviderBase, EmailMessage, EmailResult
from .registry import EmailProviderRegistry
from .service import EmailService
from .templates import get_email_template, EMAIL_TEMPLATES

__all__ = [
    'EmailProviderBase',
    'EmailMessage', 
    'EmailResult',
    'EmailProviderRegistry',
    'EmailService',
    'get_email_template',
    'EMAIL_TEMPLATES'
]
