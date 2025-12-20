# backend-enhanced/integrations/slack.py

"""
Slack Integration Module

This module handles Slack API interactions, webhooks, and OAuth flows for integrating
Slack with other services like Google Calendar, Jira, Zoom, and Email. It includes
secure handling of tokens, event processing, and user interactions via Slack commands
and messages.

Security: Uses environment variables for sensitive data, implements OAuth2 flows,
and validates incoming webhook requests.
"""

import os
import json
import hmac
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import requests
from flask import Flask, request, jsonify, abort
from werkzeug.security import safe_str_cmp
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Slack API credentials and configuration
SLACK_CLIENT_ID = os.getenv("SLACK_CLIENT_ID", "")
SLACK_CLIENT_SECRET = os.getenv("SLACK_CLIENT_SECRET", "")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET", "")
SLACK_REDIRECT_URI = os.getenv("SLACK_REDIRECT_URI", "")
SLACK_SCOPES = "chat:write,commands,users:read,team:read"

# Initialize Flask app for webhook endpoints
app = Flask(__name__)


class SlackIntegration:
    """Class to manage Slack API interactions and integrations with other services."""

    def __init__(self):
        self.base_url = "https://slack.com/api"
        self.token_storage: Dict[str, Dict[str, Any]] = {}  # In-memory token storage (replace with DB in production)

    def get_oauth_url(self) -> str:
        """
        Generate Slack OAuth authorization URL for user consent.
        
        Returns:
            str: OAuth URL for Slack authorization.
        """
        return (
            f"https://slack.com/oauth/v2/authorize?"
            f"client_id={SLACK_CLIENT_ID}&"
            f"scope={SLACK_SCOPES}&"
            f"redirect_uri={SLACK_REDIRECT_URI}"
        )

    def handle_oauth_callback(self, code: str, state: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle Slack OAuth callback to exchange code for access token.
        
        Args:
            code (str): Authorization code from Slack.
            state (Optional[str]): State parameter for CSRF protection.
        
        Returns:
            Dict[str, Any]: Response from Slack API with access token.
        
        Raises:
            Exception: If token exchange fails.
        """
        try:
            response = requests.post(
                f"{self.base_url}/oauth.v2.access",
                data={
                    "client_id": SLACK_CLIENT_ID,
                    "client_secret": SLACK_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": SLACK_REDIRECT_URI,
                },
            )
            response_data = response.json()
            if not response_data.get("ok"):
                logger.error(f"OAuth token exchange failed: {response_data.get('error')}")
                raise Exception(f"Token exchange failed: {response_data.get('error')}")
            
            # Store token securely (in production, use a database)
            team_id = response_data.get("team", {}).get("id")
            self.token_storage[team_id] = response_data
            logger.info(f"Successfully stored token for team {team_id}")
            return response_data
        except Exception as e:
            logger.error(f"Error in OAuth callback: {str(e)}")
            raise

    def verify_webhook_signature(self, body: str, timestamp: str, signature: str) -> bool:
        """
        Verify the Slack webhook request signature to prevent spoofing.
        
        Args:
            body (str): Raw request body.
            timestamp (str): Timestamp from Slack request headers.
            signature (str): Signature from Slack request headers.
        
        Returns:
            bool: True if signature is valid, False otherwise.
        """
        try:
            # Construct the signature base string
            sig_basestring = f"v0:{timestamp}:{body}"
            # Compute the HMAC-SHA256 signature
            computed_sig = hmac.new(
                SLACK_SIGNING_SECRET.encode("utf-8"),
                sig_basestring.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()
            computed_sig = f"v0={computed_sig}"
            # Compare signatures securely
            return safe_str_cmp(computed_sig, signature)
        except Exception as e:
            logger.error(f"Signature verification failed: {str(e)}")
            return False

    def post_message(self, team_id: str, channel: str, text: str) -> Dict[str, Any]:
        """
        Post a message to a Slack channel using the stored access token.
        
        Args:
            team_id (str): Slack team ID.
            channel (str): Target channel ID or name.
            text (str): Message text to send.
        
        Returns:
            Dict[str, Any]: Response from Slack API.
        """
        try:
            token_data = self.token_storage.get(team_id)
            if not token_data:
                raise ValueError(f"No token found for team {team_id}")
            
            access_token = token_data.get("authed_user", {}).get("access_token")
            response = requests.post(
                f"{self.base_url}/chat.postMessage",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"channel": channel, "text": text},
            )
            return response.json()
        except Exception as e:
            logger.error(f"Error posting message to Slack: {str(e)}")
            raise

    def handle_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming Slack events (e.g., messages, commands).
        
        Args:
            event_data (Dict[str, Any]): Event payload from Slack.
        
        Returns:
            Dict[str, Any]: Response to the event.
        """
        try:
            event_type = event_data.get("type")
            if event_type == "url_verification":
                return {"challenge": event_data.get("challenge")}
            
            event_inner = event_data.get("event", {})
            if event_inner.get("type") == "app_mention":
                team_id = event_data.get("team_id")
                channel = event_inner.get("channel")
                text = "Hello! How can I assist you with integrations today?"
                return self.post_message(team_id, channel, text)
            
            return {"status": "event_processed"}
        except Exception as e:
            logger.error(f"Error handling Slack event: {str(e)}")
            return {"error": str(e)}


# Flask endpoint for Slack events webhook
@app.route("/slack/events", methods=["POST"])
def slack_events():
    """
    Endpoint to handle Slack events webhook requests.
    Validates signature and processes events.
    """
    try:
        # Get headers for signature verification
        timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
        signature = request.headers.get("X-Slack-Signature", "")
        body = request.get_data(as_text=True)

        # Check if request is too old (replay attack prevention)
        if abs(int(timestamp) - int(datetime.now().timestamp())) > 60 * 5:
            abort(403, description="Request timestamp too old")

        # Verify signature
        slack_integration = SlackIntegration()
        if not slack_integration.verify_webhook_signature(body, timestamp, signature):
            abort(403, description="Invalid signature")

        # Parse request data
        data = request.get_json()
        if not data:
            abort(400, description="Invalid JSON payload")

        # Handle event
        response = slack_integration.handle_event(data)
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error in Slack events endpoint: {str(e)}")
        abort(500, description="Internal server error")


# Flask endpoint for Slack OAuth callback
@app.route("/slack/oauth/callback", methods=["GET"])
def slack_oauth_callback():
    """
    Endpoint to handle Slack OAuth callback after user authorization.
    """
    try:
        code = request.args.get("code")
        state = request.args.get("state")
        if not code:
            abort(400, description="Missing authorization code")

        slack_integration = SlackIntegration()
        response = slack_integration.handle_oauth_callback(code, state)
        return jsonify({"status": "success", "data": response})
    except Exception as e:
        logger.error(f"Error in Slack OAuth callback endpoint: {str(e)}")
        abort(500, description="OAuth process failed")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)