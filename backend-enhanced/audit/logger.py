# backend-enhanced/audit/logger.py
"""
Audit Logger Module for Enterprise Features

This module provides a secure, comprehensive audit logging system for tracking
user actions, system events, and security-related activities in a multi-tenant
environment. It supports integration with SSO (SAML, OAuth2), RBAC, and ensures
data encryption for sensitive log entries.

Features:
- Secure logging with encryption for sensitive data
- Multi-tenancy support with tenant isolation
- Detailed audit trails for user actions and system events
- Integration with RBAC for role-based logging context
- Error handling and log rotation
- Compliance with enterprise security standards
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
import os
from pathlib import Path
import threading
from cryptography.fernet import Fernet
from logging.handlers import RotatingFileHandler
import uuid

# Constants for configuration
LOG_DIR = Path("logs/audit")
LOG_FILE = LOG_DIR / "audit.log"
MAX_BYTES = 10 * 1024 * 1024  # 10MB per log file
BACKUP_COUNT = 5  # Number of backup files to keep
ENCRYPTION_KEY_FILE = LOG_DIR / "encryption_key.key"

# Thread-local storage for tenant context
_thread_local = threading.local()


class AuditLogger:
    """
    A secure audit logger for enterprise applications with support for
    multi-tenancy, encryption, and detailed event tracking.
    """

    def __init__(self, app_name: str = "EnterpriseApp"):
        """
        Initialize the AuditLogger with encryption and file rotation.

        Args:
            app_name (str): Name of the application for log identification.
        """
        self.app_name = app_name
        self.logger = logging.getLogger("AuditLogger")
        self.logger.setLevel(logging.INFO)

        # Ensure log directory exists
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        # Initialize encryption
        self._initialize_encryption()

        # Set up rotating file handler
        self._setup_handlers()

    def _initialize_encryption(self) -> None:
        """
        Initialize encryption for sensitive log data.
        Loads or generates an encryption key for securing log entries.
        """
        try:
            if not ENCRYPTION_KEY_FILE.exists():
                key = Fernet.generate_key()
                with open(ENCRYPTION_KEY_FILE, "wb") as key_file:
                    key_file.write(key)
                # Restrict file permissions to owner only
                os.chmod(ENCRYPTION_KEY_FILE, 0o600)
            else:
                with open(ENCRYPTION_KEY_FILE, "rb") as key_file:
                    key = key_file.read()
            self.cipher_suite = Fernet(key)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize encryption for audit logger: {str(e)}")

    def _setup_handlers(self) -> None:
        """
        Set up logging handlers with rotation and formatting.
        """
        try:
            # Remove existing handlers to prevent duplicates
            self.logger.handlers = []

            # Custom JSON formatter for structured logging
            formatter = logging.Formatter(
                json.dumps({
                    "timestamp": "%(asctime)s",
                    "level": "%(levelname)s",
                    "app": self.app_name,
                    "message": "%(message)s"
                }, default=str)
            )

            # Rotating file handler for audit logs
            file_handler = RotatingFileHandler(
                filename=LOG_FILE,
                maxBytes=MAX_BYTES,
                backupCount=BACKUP_COUNT
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

            # Console handler for debugging (optional, can be disabled in production)
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        except Exception as e:
            raise RuntimeError(f"Failed to set up audit logger handlers: {str(e)}")

    def set_tenant_context(self, tenant_id: str) -> None:
        """
        Set the tenant context for the current thread to ensure logs are
        associated with the correct tenant in a multi-tenant environment.

        Args:
            tenant_id (str): Unique identifier for the tenant.
        """
        _thread_local.tenant_id = tenant_id

    def get_tenant_context(self) -> Optional[str]:
        """
        Retrieve the tenant context for the current thread.

        Returns:
            Optional[str]: Tenant ID if set, None otherwise.
        """
        return getattr(_thread_local, 'tenant_id', None)

    def encrypt_sensitive_data(self, data: str) -> str:
        """
        Encrypt sensitive data before logging.

        Args:
            data (str): Sensitive data to encrypt.

        Returns:
            str: Encrypted data as a string.
        """
        try:
            return self.cipher_suite.encrypt(data.encode()).decode()
        except Exception as e:
            self.logger.error(f"Encryption failed for sensitive data: {str(e)}")
            return "[ENCRYPTION_FAILED]"

    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data from logs (for authorized access only).

        Args:
            encrypted_data (str): Encrypted data to decrypt.

        Returns:
            str: Decrypted data or error message if decryption fails.
        """
        try:
            return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            self.logger.error(f"Decryption failed for sensitive data: {str(e)}")
            return "[DECRYPTION_FAILED]"

    def log_event(
        self,
        event_type: str,
        user_id: str,
        action: str,
        resource: str,
        status: str,
        details: Dict[str, Any] = None,
        sensitive_data: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Log an audit event with detailed context for tracking user actions
        and system events.

        Args:
            event_type (str): Type of event (e.g., 'AUTH', 'ACCESS', 'SYSTEM').
            user_id (str): Identifier of the user performing the action.
            action (str): Action performed (e.g., 'LOGIN', 'UPDATE', 'DELETE').
            resource (str): Resource affected by the action.
            status (str): Status of the action (e.g., 'SUCCESS', 'FAILURE').
            details (Dict[str, Any], optional): Additional event details.
            sensitive_data (Dict[str, str], optional): Sensitive data to encrypt.
        """
        try:
            tenant_id = self.get_tenant_context() or "UNKNOWN_TENANT"
            event_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()

            # Prepare log entry
            log_entry = {
                "event_id": event_id,
                "event_type": event_type,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "action": action,
                "resource": resource,
                "status": status,
                "timestamp": timestamp,
                "details": details or {}
            }

            # Encrypt sensitive data if provided
            if sensitive_data:
                encrypted_data = {
                    key: self.encrypt_sensitive_data(value)
                    for key, value in sensitive_data.items()
                }
                log_entry["sensitive_data"] = encrypted_data

            # Log the event as structured JSON
            self.logger.info(json.dumps(log_entry, default=str))

        except Exception as e:
            self.logger.error(f"Failed to log audit event: {str(e)}")

    def log_auth_event(
        self,
        user_id: str,
        auth_method: str,
        status: str,
        ip_address: str,
        user_agent: str
    ) -> None:
        """
        Log authentication events (e.g., SSO login via SAML/OAuth2).

        Args:
            user_id (str): Identifier of the user attempting authentication.
            auth_method (str): Authentication method (e.g., 'SAML', 'OAuth2').
            status (str): Authentication status ('SUCCESS', 'FAILURE').
            ip_address (str): Client IP address.
            user_agent (str): Client user agent string.
        """
        details = {
            "auth_method": auth_method,
            "ip_address": ip_address,
            "user_agent": user_agent
        }
        sensitive_data = {"ip_address": ip_address}
        self.log_event(
            event_type="AUTH",
            user_id=user_id,
            action="LOGIN",
            resource="SYSTEM",
            status=status,
            details=details,
            sensitive_data=sensitive_data
        )

    def log_access_event(
        self,
        user_id: str,
        role: str,
        action: str,
        resource: str,
        status: str
    ) -> None:
        """
        Log access control events for RBAC tracking.

        Args:
            user_id (str): Identifier of the user.
            role (str): Role of the user under RBAC.
            action (str): Action attempted (e.g., 'READ', 'WRITE').
            resource (str): Resource accessed.
            status (str): Access status ('ALLOWED', 'DENIED').
        """
        details = {"role": role}
        self.log_event(
            event_type="ACCESS",
            user_id=user_id,
            action=action,
            resource=resource,
            status=status,
            details=details
        )


# Singleton instance for global access
audit_logger = AuditLogger()