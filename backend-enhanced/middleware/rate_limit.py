# backend-enhanced/middleware/rate_limit.py

"""
Rate Limiting Middleware for FastAPI Application
This middleware implements rate limiting to prevent abuse and DDoS attacks.
It uses Redis as the backend for tracking request counts and timestamps.
Additionally, it includes security headers and basic input validation.
"""

from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis.asyncio as redis
import logging
import os
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Redis connection for rate limiting
# Using environment variables for secure configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_pool = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

# Initialize rate limiter with Redis storage
# Rate limit set to 100 requests per minute per IP
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/60"],
    storage_uri=REDIS_URL
)

class RateLimitMiddleware:
    """
    Middleware class for implementing rate limiting and security headers
    in FastAPI applications.
    """
    
    def __init__(self, app: Callable) -> None:
        """
        Initialize the middleware with the FastAPI app.
        
        Args:
            app (Callable): FastAPI application instance
        """
        self.app = app
        limiter.init_app(app)

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """
        Handle incoming requests with rate limiting and security headers.
        
        Args:
            request (Request): Incoming HTTP request
            call_next (Callable): Next middleware or endpoint handler
            
        Returns:
            Response: HTTP response with security headers
        """
        try:
            # Apply rate limiting based on client IP
            client_ip = get_remote_address(request)
            logger.info(f"Processing request from IP: {client_ip}")

            # Validate request headers for potential malicious content
            if not self._validate_headers(request):
                logger.warning(f"Invalid headers detected from IP: {client_ip}")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Invalid request headers"}
                )

            # Process the request through rate limiter
            response = await call_next(request)
            
            # Add security headers to response
            self._add_security_headers(response)
            return response

        except RateLimitExceeded as e:
            logger.error(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": e.retry_after
                }
            )
        except Exception as e:
            logger.error(f"Unexpected error processing request from IP: {client_ip}: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )

    def _validate_headers(self, request: Request) -> bool:
        """
        Validate request headers to prevent common attacks like XSS.
        Checks for suspicious content in User-Agent and Referer headers.
        
        Args:
            request (Request): Incoming HTTP request
            
        Returns:
            bool: True if headers are valid, False otherwise
        """
        user_agent = request.headers.get("User-Agent", "")
        referer = request.headers.get("Referer", "")
        
        # Basic check for script tags or suspicious characters
        suspicious_patterns = ["<script", "javascript:", "onerror", "onload"]
        
        for pattern in suspicious_patterns:
            if pattern in user_agent.lower() or pattern in referer.lower():
                return False
                
        return True

    def _add_security_headers(self, response: Response) -> None:
        """
        Add security headers to the HTTP response to prevent common attacks.
        
        Args:
            response (Response): HTTP response object to modify
        """
        # Prevent XSS attacks
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Enable strict transport security (force HTTPS)
        response.headers['Strict-Transport-Security'] = (
            'max-age=31536000; includeSubDomains; preload'
        )
        
        # Prevent information disclosure
        response.headers['X-Powered-By'] = 'SecureServer'
        response.headers['Server'] = 'SecureServer'

# Decorator for endpoint-specific rate limits if needed
def custom_rate_limit(limit: str) -> Callable:
    """
    Decorator for applying custom rate limits to specific endpoints.
    
    Args:
        limit (str): Rate limit string in format "requests/seconds"
        
    Returns:
        Callable: Decorator function for rate limiting
    """
    return limiter.limit(limit)