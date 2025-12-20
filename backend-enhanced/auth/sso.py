# backend-enhanced/auth/sso.py
"""
Single Sign-On (SSO) implementation for enterprise authentication.
Supports SAML and OAuth2 protocols with multi-tenancy, RBAC, audit logging,
and encryption for secure authentication flows.
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import jwt
from cryptography.fernet import Fernet
from fastapi import HTTPException, status
from pydantic import BaseModel
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
import requests
from sqlalchemy.orm import Session

from app.models.user import User, Tenant, Role
from app.models.audit import AuditLog
from app.config import settings
from app.utils.security import generate_random_key

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Encryption key for sensitive data (should be stored securely in production)
ENCRYPTION_KEY = Fernet.generate_key()
cipher_suite = Fernet(ENCRYPTION_KEY)


class SSOConfig(BaseModel):
    """Configuration model for SSO providers."""
    provider_type: str  # 'saml' or 'oauth2'
    client_id: str
    client_secret: str
    redirect_uri: str
    metadata_url: Optional[str] = None  # For SAML
    authorization_url: Optional[str] = None  # For OAuth2
    token_url: Optional[str] = None  # For OAuth2


class SSOAuth:
    """Handles SSO authentication for SAML and OAuth2 providers."""
    
    def __init__(self, config: SSOConfig):
        self.config = config
        self.provider_type = config.provider_type.lower()
        if self.provider_type not in ['saml', 'oauth2']:
            raise ValueError(f"Unsupported SSO provider type: {self.provider_type}")

    def encrypt_sensitive_data(self, data: str) -> bytes:
        """Encrypt sensitive data using Fernet symmetric encryption."""
        try:
            return cipher_suite.encrypt(data.encode())
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Encryption error"
            )

    def decrypt_sensitive_data(self, encrypted_data: bytes) -> str:
        """Decrypt sensitive data using Fernet symmetric encryption."""
        try:
            return cipher_suite.decrypt(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Decryption error"
            )

    def get_saml_metadata(self) -> Dict[str, Any]:
        """
        Fetch and parse SAML metadata from the provider's metadata URL.
        Returns relevant configuration details.
        """
        if self.provider_type != 'saml' or not self.config.metadata_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SAML metadata URL not configured"
            )

        try:
            response = requests.get(self.config.metadata_url, timeout=10)
            response.raise_for_status()
            metadata = ET.fromstring(response.content)
            # Extract relevant SAML metadata (simplified for example)
            entity_id = metadata.get('entityID', '')
            sso_url = metadata.find(
                ".//{urn:oasis:names:tc:SAML:2.0:metadata}SingleSignOnService"
            ).get('Location', '')
            return {'entity_id': entity_id, 'sso_url': sso_url}
        except Exception as e:
            logger.error(f"Failed to fetch SAML metadata: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unable to fetch SAML metadata"
            )

    def initiate_saml_auth(self) -> str:
        """Initiate SAML authentication by generating a redirect URL."""
        metadata = self.get_saml_metadata()
        sso_url = metadata.get('sso_url', '')
        if not sso_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SAML SSO URL not found in metadata"
            )
        # Simplified SAML AuthnRequest (in production, use a full SAML library like python-saml)
        auth_request = {
            'SAMLRequest': 'encoded_saml_request',  # Placeholder for encoded request
            'RelayState': self.config.redirect_uri
        }
        redirect_url = f"{sso_url}?{urlencode(auth_request)}"
        logger.info(f"Initiating SAML auth redirect to: {sso_url}")
        return redirect_url

    def initiate_oauth2_auth(self) -> str:
        """Initiate OAuth2 authentication by generating a redirect URL."""
        if self.provider_type != 'oauth2' or not self.config.authorization_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OAuth2 authorization URL not configured"
            )

        params = {
            'client_id': self.config.client_id,
            'redirect_uri': self.config.redirect_uri,
            'response_type': 'code',
            'scope': 'openid profile email'
        }
        redirect_url = f"{self.config.authorization_url}?{urlencode(params)}"
        logger.info(f"Initiating OAuth2 auth redirect to: {self.config.authorization_url}")
        return redirect_url

    def handle_oauth2_callback(self, code: str) -> Dict[str, Any]:
        """Handle OAuth2 callback, exchange code for token, and fetch user info."""
        if self.provider_type != 'oauth2' or not self.config.token_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OAuth2 token URL not configured"
            )

        try:
            payload = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': self.config.redirect_uri,
                'client_id': self.config.client_id,
                'client_secret': self.config.client_secret
            }
            response = requests.post(self.config.token_url, data=payload, timeout=10)
            response.raise_for_status()
            token_data = response.json()
            access_token = token_data.get('access_token')
            if not access_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to obtain access token"
                )
            return token_data
        except Exception as e:
            logger.error(f"OAuth2 token exchange failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to exchange OAuth2 code for token"
            )

    def generate_jwt_token(self, user_data: Dict[str, Any], tenant_id: str) -> str:
        """
        Generate a JWT token for the authenticated user with tenant and role information.
        """
        try:
            payload = {
                'sub': user_data.get('email', ''),
                'name': user_data.get('name', ''),
                'tenant_id': tenant_id,
                'roles': user_data.get('roles', []),
                'exp': datetime.utcnow() + timedelta(hours=24),
                'iat': datetime.utcnow()
            }
            token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm='HS256')
            logger.info(f"Generated JWT token for user: {user_data.get('email')}")
            return token
        except Exception as e:
            logger.error(f"JWT token generation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate authentication token"
            )


class SSOUserManager:
    """Manages user provisioning, RBAC, and multi-tenancy for SSO users."""
    
    def __init__(self, db_session: Session):
        self.db = db_session

    def provision_user(self, user_data: Dict[str, Any], tenant_id: str) -> User:
        """
        Provision or update a user in the database based on SSO data.
        Assigns tenant and default roles.
        """
        try:
            email = user_data.get('email')
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email not provided in SSO data"
                )

            user = self.db.query(User).filter(User.email == email).first()
            if not user:
                user = User(
                    email=email,
                    name=user_data.get('name', ''),
                    tenant_id=tenant_id,
                    is_active=True
                )
                self.db.add(user)
                self.db.commit()
                self.db.refresh(user)
                logger.info(f"Provisioned new user: {email}")
            else:
                user.name = user_data.get('name', user.name)
                user.tenant_id = tenant_id
                self.db.commit()
                self.db.refresh(user)
                logger.info(f"Updated existing user: {email}")

            # Assign default role if none exists
            if not user.roles:
                default_role = self.db.query(Role).filter(
                    Role.name == 'user', Role.tenant_id == tenant_id
                ).first()
                if default_role:
                    user.roles.append(default_role)
                    self.db.commit()
                    logger.info(f"Assigned default role to user: {email}")

            return user
        except Exception as e:
            self.db.rollback()
            logger.error(f"User provisioning failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to provision user"
            )

    def log_audit_event(self, user_id: str, event_type: str, details: str):
        """Log authentication and authorization events for audit purposes."""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                event_type=event_type,
                details=details,
                timestamp=datetime.utcnow()
            )
            self.db.add(audit_log)
            self.db.commit()
            logger.info(f"Audit event logged: {event_type} for user {user_id}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Audit logging failed: {str(e)}")


def get_sso_auth(provider_config: SSOConfig) -> SSOAuth:
    """Factory function to create an SSOAuth instance."""
    return SSOAuth(provider_config)


def get_sso_user_manager(db_session: Session) -> SSOUserManager:
    """Factory function to create an SSOUserManager instance."""
    return SSOUserManager(db_session)