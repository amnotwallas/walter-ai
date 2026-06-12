"""
Security and API protection module.
Implements token validation mechanisms and rate limiting
to ensure access is authorized and controlled.
"""

from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from app.core.config import get_settings
from slowapi import Limiter
from slowapi.util import get_remote_address

settings = get_settings()

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

limiter = Limiter(key_func=get_remote_address)

async def validate_api_key(api_key: str = Security(api_key_header)):
    """
    Validates that the token sent in the header matches the configured key.

    Args:
        api_key (str): The token extracted from the 'X-API-KEY' header.

    Returns:
        str: The API key if valid.

    Raises:
        HTTPException: If the API key is null or does not match, blocking access.
    """
    if api_key == settings.API_KEY:
        return api_key
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="CRITICAL_ERROR: INVALID_API_KEY. ACCESS_DENIED."
    )
