# backend-enhanced/middleware/security.py

"""
Security middleware for FastAPI application.
Implements input validation, rate limiting, security headers,
and protection against XSS and CSRF attacks.
"""

from typing import Callable, Dict, Any
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import re
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize rate limiter with Redis backend (assumes Redis is configured)
limiter = Limiter(key_func=get_remote_address)

# Security configuration constants
MAX_INPUT_LENGTH = 1000
ALLOWED_CONTENT_TYPES = {"application/json", "multipart/form-data"}
SECURE_COOKIES = {
    "secure": True,  # Only send cookies over HTTPS
    "httponly": True,  # Prevent client-side access to cookies
    "samesite": "strict",  # Prevent CSRF by restricting cookie sending
}

# Regular expression for basic input sanitization
SANITIZE_PATTERN = re.compile(r'<[^>]+>|script|javascript|on\w*=', re.IGNORECASE)


class SecurityMiddleware:
    """
    Middleware class to handle security-related concerns for incoming requests.
    Includes input validation, rate limiting, and security headers.
    """

    def __init__(self, app):
        self.app = app
        self.rate_limit_config = "5 per minute"  # Default rate limit

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """
        Process incoming requests through security checks before passing to the application.
        
        Args:
            request (Request): Incoming HTTP request
            call_next (Callable): Next middleware or endpoint handler
            
        Returns:
            Response: HTTP response with security headers
        """
        try:
            # Perform security checks
            self._validate_content_type(request)
            await self._validate_input(request)
            await self._apply_rate_limiting(request)

            # Process the request through the application
            response = await call_next(request)

            # Add security headers to the response
            self._add_security_headers(response)
            return response

        except RateLimitExceeded:
            logger.warning(f"Rate limit exceeded for client: {request.client.host}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests. Please try again later."}
            )
        except HTTPException as e:
            logger.error(f"Security validation failed: {str(e)}")
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        except Exception as e:
            logger.error(f"Unexpected error in security middleware: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )

    def _validate_content_type(self, request: Request) -> None:
        """
        Validate the Content-Type header of the request to prevent unexpected data formats.
        
        Args:
            request (Request): Incoming HTTP request
            
        Raises:
            HTTPException: If Content-Type is not allowed
        """
        content_type = request.headers.get("Content-Type", "").split(";")[0].strip()
        if content_type and content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Content-Type header"
            )

    async def _validate_input(self, request: Request) -> None:
        """
        Validate and sanitize input data from request body and query parameters.
        Prevents XSS by checking for malicious content.
        
        Args:
            request (Request): Incoming HTTP request
            
        Raises:
            HTTPException: If input validation fails
        """
        try:
            # Check query parameters
            for key, value in request.query_params.items():
                if len(value) > MAX_INPUT_LENGTH:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Query parameter {key} exceeds maximum length"
                    )
                if SANITIZE_PATTERN.search(value):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid input detected in query parameter {key}"
                    )

            # Check request body if it exists
            if request.headers.get("Content-Type", "").startswith("application/json"):
                body = await request.json()
                self._recursive_validate_body(body)
        except Exception as e:
            logger.error(f"Input validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid request body format"
            )

    def _recursive_validate_body(self, data: Any, depth: int = 0, max_depth: int = 10) -> None:
        """
        Recursively validate nested structures in request body.
        
        Args:
            data (Any): Data to validate
            depth (int): Current recursion depth
            max_depth (int): Maximum allowed recursion depth
            
        Raises:
            HTTPException: If validation fails or max depth is exceeded
        """
        if depth > max_depth:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request body nesting too deep"
            )

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    self._recursive_validate_body(value, depth + 1, max_depth)
                elif isinstance(value, str):
                    if len(value) > MAX_INPUT_LENGTH:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Field {key} exceeds maximum length"
                        )
                    if SANITIZE_PATTERN.search(value):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid input detected in field {key}"
                        )
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    self._recursive_validate_body(item, depth + 1, max_depth)

    async def _apply_rate_limiting(self, request: Request) -> None:
        """
        Apply rate limiting to prevent abuse of the API.
        Uses slowapi with Redis backend for distributed rate limiting.
        
        Args:
            request (Request): Incoming HTTP request
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        @limiter.limit(self.rate_limit_config)
        async def rate_limit_handler(request: Request):
            pass
        
        await rate_limit_handler(request)

    def _add_security_headers(self, response: Response) -> None:
        """
        Add security-related HTTP headers to the response.
        Includes protections against XSS, clickjacking, and MIME sniffing.
        
        Args:
            response (Response): HTTP response to modify
        """
        response.headers.update({
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; object-src 'none';",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "no-referrer",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
        })

        # Apply secure cookie settings if cookies are present
        for cookie in response.headers.getlist("Set-Cookie"):
            updated_cookie = cookie
            for key, value in SECURE_COOKIES.items():
                if isinstance(value, bool):
                    if value and key not in updated_cookie.lower():
                        updated_cookie += f"; {key}"
                else:
                    if f"{key}=" not in updated_cookie.lower():
                        updated_cookie += f"; {key}={value}"
            response.headers.append("Set-Cookie", updated_cookie)


def setup_security_middleware(app) -> None:
    """
    Setup function to register security middleware with the FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(SecurityMiddleware)
    logger.info("Security middleware registered with application")