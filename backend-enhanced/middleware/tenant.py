# backend-enhanced/middleware/tenant.py
"""
Tenant Middleware for Multi-Tenancy Support

This middleware handles tenant identification and context setting for multi-tenant applications.
It supports tenant isolation, integrates with RBAC, and ensures secure tenant-specific data access.
"""

from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel
import logging
import jwt
from datetime import datetime
import threading
from contextvars import ContextVar

# Configure logging for audit purposes
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thread-local storage for tenant context
_tenant_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar('tenant_context', default=None)

class TenantConfig(BaseModel):
    """Configuration model for tenant-specific settings."""
    tenant_id: str
    tenant_name: str
    database_url: Optional[str] = None
    encryption_key: Optional[str] = None
    allowed_roles: list[str] = []

class TenantMiddleware:
    """
    Middleware to handle tenant identification and context management.
    Ensures requests are routed to the correct tenant context and enforces isolation.
    """
    
    def __init__(self, app, tenant_configs: Dict[str, TenantConfig], jwt_secret: str):
        """
        Initialize the Tenant Middleware.
        
        Args:
            app: FastAPI application instance
            tenant_configs: Dictionary of tenant configurations mapped by tenant_id
            jwt_secret: Secret key for decoding JWT tokens
        """
        self.app = app
        self.tenant_configs = tenant_configs
        self.jwt_secret = jwt_secret

    async def __call__(self, request: Request, call_next) -> Response:
        """
        Process incoming requests to identify tenant and set context.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or endpoint in the chain
            
        Returns:
            Response: HTTP response after processing the request
        """
        try:
            tenant_id = self._extract_tenant_id(request)
            if not tenant_id or tenant_id not in self.tenant_configs:
                logger.error(f"Invalid or missing tenant ID: {tenant_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid or missing tenant information"
                )

            # Set tenant context for the current request
            tenant_config = self.tenant_configs[tenant_id]
            tenant_data = {
                "tenant_id": tenant_id,
                "tenant_name": tenant_config.tenant_name,
                "database_url": tenant_config.database_url,
                "encryption_key": tenant_config.encryption_key,
                "allowed_roles": tenant_config.allowed_roles
            }
            token = _tenant_context.set(tenant_data)

            # Log tenant access for audit purposes
            logger.info(
                f"Tenant context set for tenant_id={tenant_id}, tenant_name={tenant_config.tenant_name}, "
                f"request_path={request.url.path}, client_ip={request.client.host}"
            )

            # Process the request with the tenant context
            response = await call_next(request)

            # Reset tenant context after request processing
            _tenant_context.reset(token)
            return response

        except HTTPException as http_err:
            logger.error(f"HTTP error in tenant middleware: {str(http_err.detail)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in tenant middleware: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during tenant processing"
            )

    def _extract_tenant_id(self, request: Request) -> Optional[str]:
        """
        Extract tenant ID from request headers or JWT token.
        Supports multiple methods for tenant identification.
        
        Args:
            request: Incoming HTTP request
            
        Returns:
            Optional[str]: Tenant ID if found, None otherwise
        """
        # Method 1: Check for explicit tenant ID in headers (for API clients)
        tenant_id = request.headers.get('X-Tenant-ID')
        if tenant_id:
            return tenant_id

        # Method 2: Extract from JWT token in Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                decoded_token = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
                tenant_id = decoded_token.get('tenant_id')
                if tenant_id:
                    return tenant_id
            except jwt.InvalidTokenError as e:
                logger.warning(f"Invalid JWT token for tenant identification: {str(e)}")
                return None

        # Method 3: Fallback to subdomain if configured
        host = request.headers.get('Host', '')
        subdomain = host.split('.')[0] if '.' in host else ''
        if subdomain in self.tenant_configs:
            return subdomain

        return None

def get_current_tenant() -> Optional[Dict[str, Any]]:
    """
    Get the current tenant context for the request.
    This function is thread-safe and uses context variables.
    
    Returns:
        Optional[Dict[str, Any]]: Current tenant context if set, None otherwise
    """
    return _tenant_context.get()

def validate_tenant_role(required_roles: list[str]) -> bool:
    """
    Validate if the current tenant user has the required roles.
    Integrates with RBAC system.
    
    Args:
        required_roles: List of roles required for access
        
    Returns:
        bool: True if user has required roles, False otherwise
    """
    tenant_data = get_current_tenant()
    if not tenant_data:
        logger.warning("No tenant context available for role validation")
        return False

    allowed_roles = tenant_data.get('allowed_roles', [])
    return any(role in allowed_roles for role in required_roles)

def log_tenant_activity(action: str, details: Dict[str, Any] = None):
    """
    Log tenant-specific activity for audit purposes.
    
    Args:
        action: Action being performed (e.g., 'data_access', 'config_update')
        details: Additional details about the activity
    """
    tenant_data = get_current_tenant()
    tenant_id = tenant_data.get('tenant_id', 'unknown') if tenant_data else 'unknown'
    tenant_name = tenant_data.get('tenant_name', 'unknown') if tenant_data else 'unknown'
    timestamp = datetime.utcnow().isoformat()
    
    log_entry = {
        "timestamp": timestamp,
        "tenant_id": tenant_id,
        "tenant_name": tenant_name,
        "action": action,
        "details": details or {}
    }
    logger.info(f"Audit Log: {log_entry}")

# Example usage in FastAPI application (for reference)
"""
from fastapi import FastAPI

app = FastAPI()

# Sample tenant configurations
tenant_configs = {
    "tenant1": TenantConfig(
        tenant_id="tenant1",
        tenant_name="Tenant One",
        database_url="postgresql://user:pass@localhost/tenant1_db",
        encryption_key="supersecretkey1",
        allowed_roles=["admin", "user"]
    ),
    "tenant2": TenantConfig(
        tenant_id="tenant2",
        tenant_name="Tenant Two",
        database_url="postgresql://user:pass@localhost/tenant2_db",
        encryption_key="supersecretkey2",
        allowed_roles=["user"]
    )
}

# Add middleware to FastAPI app
app.add_middleware(TenantMiddleware, tenant_configs=tenant_configs, jwt_secret="your_jwt_secret_here")
"""