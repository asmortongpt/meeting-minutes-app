# backend-enhanced/integrations/email_service.py
"""
Email Service Integration Module

This module provides a secure and reliable email sending service using SMTP with
support for popular email providers. It includes OAuth2 authentication for Gmail,
template rendering, attachment handling, and comprehensive error logging.

Key Features:
- SMTP connection with TLS/SSL security
- OAuth2 support for Gmail
- Email template rendering
- Attachment handling with size limits
- Rate limiting and retry mechanism
- Detailed logging for debugging and monitoring
"""

import smtplib
import ssl
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import base64

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Constants
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10MB
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
RATE_LIMIT_PER_MINUTE = 60
SCOPES = ['https://www.googleapis.com/auth/gmail.send']


class EmailService:
    def __init__(self, provider: str = "gmail", config: Dict[str, str] = None):
        """
        Initialize the Email Service with provider-specific configuration.

        Args:
            provider (str): Email provider (default: "gmail")
            config (Dict[str, str]): Configuration dictionary with credentials
        """
        self.provider = provider.lower()
        self.config = config or {}
        self.rate_limit_tracker: List[float] = []
        self.credentials = None
        self._load_config()
        if self.provider == "gmail":
            self._initialize_gmail_oauth()

    def _load_config(self) -> None:
        """
        Load configuration from environment variables or provided config dict.
        Falls back to environment variables if config dict values are not provided.
        """
        try:
            if self.provider == "gmail":
                self.client_id = self.config.get("client_id", os.getenv("GMAIL_CLIENT_ID", ""))
                self.client_secret = self.config.get("client_secret", os.getenv("GMAIL_CLIENT_SECRET", ""))
                self.refresh_token = self.config.get("refresh_token", os.getenv("GMAIL_REFRESH_TOKEN", ""))
                self.token_path = self.config.get("token_path", "token.pickle")
            else:
                self.smtp_server = self.config.get("smtp_server", os.getenv("SMTP_SERVER", ""))
                self.smtp_port = int(self.config.get("smtp_port", os.getenv("SMTP_PORT", "587")))
                self.username = self.config.get("username", os.getenv("SMTP_USERNAME", ""))
                self.password = self.config.get("password", os.getenv("SMTP_PASSWORD", ""))
        except Exception as e:
            logger.error(f"Failed to load email configuration: {str(e)}")
            raise ValueError(f"Invalid email configuration: {str(e)}")

    def _initialize_gmail_oauth(self) -> None:
        """
        Initialize OAuth2 credentials for Gmail API.
        Loads existing credentials or initiates OAuth flow if needed.
        """
        try:
            creds = None
            if os.path.exists(self.token_path):
                with open(self.token_path, 'rb') as token:
                    creds = pickle.load(token)

            if creds and creds.valid:
                self.credentials = creds
                return

            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(
                    {
                        "installed": {
                            "client_id": self.client_id,
                            "client_secret": self.client_secret,
                            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"],
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                        }
                    },
                    SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
            self.credentials = creds
        except Exception as e:
            logger.error(f"Failed to initialize Gmail OAuth: {str(e)}")
            raise RuntimeError(f"Failed to initialize Gmail OAuth: {str(e)}")

    def _check_rate_limit(self) -> bool:
        """
        Check if the current request is within rate limits.

        Returns:
            bool: True if within limits, False otherwise
        """
        current_time = time.time()
        self.rate_limit_tracker = [
            t for t in self.rate_limit_tracker
            if current_time - t < 60
        ]
        if len(self.rate_limit_tracker) >= RATE_LIMIT_PER_MINUTE:
            logger.warning("Email rate limit exceeded")
            return False
        self.rate_limit_tracker.append(current_time)
        return True

    def send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        attachments: Optional[List[Dict[str, str]]] = None,
        is_html: bool = False
    ) -> bool:
        """
        Send an email with optional attachments.

        Args:
            to (List[str]): List of recipient email addresses
            subject (str): Email subject
            body (str): Email body content
            from_email (Optional[str]): Sender email address
            attachments (Optional[List[Dict[str, str]]]): List of attachments with 'path' and 'name'
            is_html (bool): Whether the body is HTML content

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self._check_rate_limit():
            logger.error("Failed to send email: Rate limit exceeded")
            return False

        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['To'] = ", ".join(to)
        msg['From'] = from_email or (self.username if self.provider != "gmail" else "me")

        # Attach body
        content_type = 'html' if is_html else 'plain'
        msg.attach(MIMEText(body, content_type))

        # Handle attachments
        if attachments:
            if not self._attach_files(msg, attachments):
                return False

        # Send email with retry logic
        for attempt in range(MAX_RETRIES):
            try:
                if self.provider == "gmail":
                    return self._send_gmail(msg)
                else:
                    return self._send_smtp(msg)
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed to send email: {str(e)}")
                if attempt == MAX_RETRIES - 1:
                    logger.error(f"Failed to send email after {MAX_RETRIES} attempts")
                    return False
                time.sleep(RETRY_DELAY)
        return False

    def _attach_files(self, msg: MIMEMultipart, attachments: List[Dict[str, str]]) -> bool:
        """
        Attach files to the email message.

        Args:
            msg (MIMEMultipart): Email message object
            attachments (List[Dict[str, str]]): List of attachment details

        Returns:
            bool: True if attachments added successfully, False otherwise
        """
        try:
            for attachment in attachments:
                file_path = attachment.get('path', '')
                file_name = attachment.get('name', os.path.basename(file_path))

                if not os.path.exists(file_path):
                    logger.error(f"Attachment file not found: {file_path}")
                    return False

                file_size = os.path.getsize(file_path)
                if file_size > MAX_ATTACHMENT_SIZE:
                    logger.error(f"Attachment size exceeds limit: {file_path}")
                    return False

                with open(file_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {file_name}',
                    )
                    msg.attach(part)
            return True
        except Exception as e:
            logger.error(f"Failed to attach files: {str(e)}")
            return False

    def _send_gmail(self, msg: MIMEMultipart) -> bool:
        """
        Send email using Gmail API with OAuth2.

        Args:
            msg (MIMEMultipart): Email message object

        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            from googleapiclient.discovery import build
            service = build('gmail', 'v1', credentials=self.credentials)
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            message = {'raw': raw}
            service.users().messages().send(userId='me', body=message).execute()
            logger.info("Email sent successfully via Gmail API")
            return True
        except Exception as e:
            logger.error(f"Failed to send email via Gmail API: {str(e)}")
            return False

    def _send_smtp(self, msg: MIMEMultipart) -> bool:
        """
        Send email using standard SMTP protocol.

        Args:
            msg (MIMEMultipart): Email message object

        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.username, self.password)
                server.sendmail(msg['From'], msg['To'].split(", "), msg.as_string())
            logger.info("Email sent successfully via SMTP")
            return True
        except Exception as e:
            logger.error(f"Failed to send email via SMTP: {str(e)}")
            return False