from .search import SearchService

# Email service import is optional - only if aiosmtplib is available
try:
    from .email import email_service
    __all__ = ["SearchService", "email_service"]
except ImportError:
    __all__ = ["SearchService"]