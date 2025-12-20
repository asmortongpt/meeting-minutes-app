# backend-enhanced/auth/rbac.py
"""
Role-Based Access Control (RBAC) implementation for enterprise features.
Supports SSO integration (SAML, OAuth2), multi-tenancy, audit logging,
and encryption for secure access management.
"""

from typing import Dict, List, Optional, Set
import logging
from datetime import datetime
import json
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import saml2
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from typing import Any

# Local imports (assuming these exist in the project structure)
from backend_enhanced.models import User, Role, Permission, Tenant, AuditLog
from backend_enhanced.config import settings
from backend_enhanced.database import get_db

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize encryption for sensitive data
encryption_key = settings.ENCRYPTION_KEY.encode()
cipher_suite = Fernet(encryption_key)


class RBACManager:
    """Manages Role-Based Access Control, SSO, and multi-tenancy for the application."""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.saml_config = self._load_saml_config()
        self.oauth_client = self._initialize_oauth_client()

    def _load_saml_config(self) -> Dict[str, Any]:
        """
        Load SAML configuration for SSO integration.
        Returns a configuration dictionary for PySAML2.
        """
        try:
            return {
                "entityid": settings.SAML_ENTITY_ID,
                "service": {
                    "sp": {
                        "endpoints": {
                            "assertion_consumer_service": [
                                (settings.SAML_ACS_URL, saml2.BINDING_HTTP_REDIRECT)
                            ]
                        },
                        "allow_unsolicited": True,
                    }
                },
                "metadata": {
                    "local": [settings.SAML_IDP_METADATA_PATH]
                },
                "key_file": settings.SAML_KEY_FILE,
                "cert_file": settings.SAML_CERT_FILE,
            }
        except Exception as e:
            logger.error(f"Failed to load SAML configuration: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SAML configuration error"
            )

    def _initialize_oauth_client(self) -> OAuth2Session:
        """
        Initialize OAuth2 client for SSO integration using client credentials flow.
        Returns an OAuth2Session instance.
        """
        try:
            client = BackendApplicationClient(client_id=settings.OAUTH_CLIENT_ID)
            oauth = OAuth2Session(client=client)
            token = oauth.fetch_token(
                token_url=settings.OAUTH_TOKEN_URL,
                client_id=settings.OAUTH_CLIENT_ID,
                client_secret=settings.OAUTH_CLIENT_SECRET
            )
            logger.info("OAuth2 client initialized successfully")
            return oauth
        except Exception as e:
            logger.error(f"Failed to initialize OAuth2 client: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OAuth2 initialization error"
            )

    def encrypt_sensitive_data(self, data: str) -> bytes:
        """
        Encrypt sensitive data using Fernet symmetric encryption.
        Args:
            data: String data to encrypt.
        Returns:
            Encrypted data as bytes.
        """
        try:
            return cipher_suite.encrypt(data.encode())
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Encryption error"
            )

    def decrypt_sensitive_data(self, encrypted_data: bytes) -> str:
        """
        Decrypt sensitive data using Fernet symmetric encryption.
        Args:
            encrypted_data: Encrypted data as bytes.
        Returns:
            Decrypted data as string.
        """
        try:
            return cipher_suite.decrypt(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Decryption error"
            )

    def get_user_roles(self, user_id: int, tenant_id: int) -> List[Role]:
        """
        Retrieve roles for a user within a specific tenant.
        Args:
            user_id: ID of the user.
            tenant_id: ID of the tenant.
        Returns:
            List of Role objects associated with the user in the tenant.
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Tenant not found"
                )

            # Filter roles by tenant
            roles = [role for role in user.roles if role.tenant_id == tenant_id]
            return roles
        except Exception as e:
            logger.error(f"Error fetching user roles: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching user roles"
            )

    def get_role_permissions(self, role_id: int) -> List[Permission]:
        """
        Retrieve permissions associated with a role.
        Args:
            role_id: ID of the role.
        Returns:
            List of Permission objects associated with the role.
        """
        try:
            role = self.db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Role not found"
                )
            return role.permissions
        except Exception as e:
            logger.error(f"Error fetching role permissions: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching role permissions"
            )

    def check_permission(self, user_id: int, tenant_id: int, permission_name: str) -> bool:
        """
        Check if a user has a specific permission within a tenant.
        Args:
            user_id: ID of the user.
            tenant_id: ID of the tenant.
            permission_name: Name of the permission to check.
        Returns:
            Boolean indicating if the user has the permission.
        """
        try:
            roles = self.get_user_roles(user_id, tenant_id)
            for role in roles:
                permissions = self.get_role_permissions(role.id)
                if any(perm.name == permission_name for perm in permissions):
                    return True
            return False
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error checking permission: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error checking permission"
            )

    def log_audit_event(self, user_id: int, tenant_id: int, action: str, details: Dict[str, Any]) -> None:
        """
        Log an audit event for tracking user actions.
        Args:
            user_id: ID of the user performing the action.
            tenant_id: ID of the tenant.
            action: Description of the action performed.
            details: Additional details about the action.
        """
        try:
            audit_log = AuditLog(
                user_id=user_id,
                tenant_id=tenant_id,
                action=action,
                details=json.dumps(details),
                timestamp=datetime.utcnow()
            )
            self.db.add(audit_log)
            self.db.commit()
            logger.info(f"Audit event logged: {action} by user {user_id} in tenant {tenant_id}")
        except Exception as e:
            logger.error(f"Failed to log audit event: {str(e)}")
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to log audit event"
            )

    def enforce_multi_tenancy(self, user_id: int, tenant_id: int) -> bool:
        """
        Enforce multi-tenancy by checking if a user belongs to a tenant.
        Args:
            user_id: ID of the user.
            tenant_id: ID of the tenant.
        Returns:
            Boolean indicating if the user has access to the tenant.
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            return any(tenant.id == tenant_id for tenant in user.tenants)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error enforcing multi-tenancy: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error enforcing multi-tenancy"
            )


def get_rbac_manager(db_session: Session = Depends(get_db)) -> RBACManager:
    """
    Dependency injection for RBACManager.
    Args:
        db_session: SQLAlchemy database session.
    Returns:
        Instance of RBACManager.
    """
    return RBACManager(db_session)