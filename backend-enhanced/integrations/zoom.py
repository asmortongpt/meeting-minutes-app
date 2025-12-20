# backend-enhanced/integrations/zoom.py
"""
Zoom Integration Module

This module handles Zoom API interactions, webhooks, and OAuth flows for meeting
creation, management, and event handling. It integrates with other services like
Google Calendar, Slack, Email, and Jira for a seamless user experience.
"""

import json
import requests
from typing import Dict, Optional, Any
from datetime import datetime
import hmac
import hashlib
import base64
from fastapi import HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.models.user import User
from app.services.google_calendar import GoogleCalendarService
from app.services.slack import SlackService
from app.services.email import EmailService
from app.services.jira import JiraService


class ZoomOAuthToken(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str
    scope: str


class ZoomMeeting(BaseModel):
    id: str
    topic: str
    start_time: str
    duration: int
    join_url: str
    host_id: str


class ZoomWebhookEvent(BaseModel):
    event: str
    payload: Dict[str, Any]
    event_ts: int


class ZoomService:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.base_url = "https://api.zoom.us/v2"
        self.oauth_url = "https://zoom.us/oauth"
        self.client_id = settings.ZOOM_CLIENT_ID
        self.client_secret = settings.ZOOM_CLIENT_SECRET
        self.redirect_uri = settings.ZOOM_REDIRECT_URI
        self.webhook_secret_token = settings.ZOOM_WEBHOOK_SECRET_TOKEN
        self.google_calendar = GoogleCalendarService()
        self.slack = SlackService()
        self.email = EmailService()
        self.jira = JiraService()

    def _get_headers(self, access_token: str) -> Dict[str, str]:
        """Generate authorization headers for Zoom API requests."""
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    def get_authorization_url(self) -> str:
        """Generate the Zoom OAuth authorization URL for user consent."""
        return (
            f"{self.oauth_url}/authorize?"
            f"response_type=code&"
            f"client_id={self.client_id}&"
            f"redirect_uri={self.redirect_uri}&"
            f"scope=meeting:write meeting:read user:read"
        )

    async def get_access_token(self, code: str) -> Optional[ZoomOAuthToken]:
        """
        Exchange authorization code for access and refresh tokens.
        """
        try:
            auth_string = f"{self.client_id}:{self.client_secret}"
            auth_header = base64.b64encode(auth_string.encode()).decode()
            headers = {
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri,
            }
            response = requests.post(f"{self.oauth_url}/token", headers=headers, data=data)
            response.raise_for_status()
            return ZoomOAuthToken(**response.json())
        except requests.RequestException as e:
            logger.error(f"Failed to get Zoom access token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to authenticate with Zoom",
            )

    async def refresh_token(self, refresh_token: str) -> Optional[ZoomOAuthToken]:
        """
        Refresh an expired access token using the refresh token.
        """
        try:
            auth_string = f"{self.client_id}:{self.client_secret}"
            auth_header = base64.b64encode(auth_string.encode()).decode()
            headers = {
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            }
            response = requests.post(f"{self.oauth_url}/token", headers=headers, data=data)
            response.raise_for_status()
            return ZoomOAuthToken(**response.json())
        except requests.RequestException as e:
            logger.error(f"Failed to refresh Zoom token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to refresh Zoom token",
            )

    async def create_meeting(
        self, user: User, topic: str, start_time: datetime, duration: int
    ) -> ZoomMeeting:
        """
        Create a Zoom meeting for the specified user.
        Integrates with Google Calendar for event creation.
        """
        try:
            if not user.zoom_access_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not authenticated with Zoom",
                )

            data = {
                "topic": topic,
                "type": 2,  # Scheduled meeting
                "start_time": start_time.isoformat(),
                "duration": duration,
                "timezone": "UTC",
                "settings": {
                    "host_video": True,
                    "participant_video": True,
                    "join_before_host": False,
                    "mute_upon_entry": True,
                    "waiting_room": True,
                },
            }
            headers = self._get_headers(user.zoom_access_token)
            response = requests.post(
                f"{self.base_url}/users/me/meetings", headers=headers, json=data
            )
            response.raise_for_status()
            meeting_data = response.json()
            meeting = ZoomMeeting(**meeting_data)

            # Integrate with Google Calendar
            await self.google_calendar.create_event(
                user=user,
                summary=topic,
                start_time=start_time,
                duration=duration,
                location=meeting.join_url,
            )

            # Notify via Slack
            await self.slack.send_message(
                channel=user.slack_channel_id or "#general",
                text=f"New Zoom meeting scheduled: {topic} at {start_time.strftime('%Y-%m-%d %H:%M')} UTC\nJoin: {meeting.join_url}",
            )

            # Send email notification
            await self.email.send_email(
                to_email=user.email,
                subject=f"Zoom Meeting: {topic}",
                body=f"A new Zoom meeting has been scheduled.\nTopic: {topic}\nTime: {start_time.strftime('%Y-%m-%d %H:%M')} UTC\nJoin: {meeting.join_url}",
            )

            return meeting
        except requests.RequestException as e:
            logger.error(f"Failed to create Zoom meeting: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create Zoom meeting",
            )

    async def handle_webhook(self, event_data: Dict[str, Any], signature: str) -> None:
        """
        Handle incoming Zoom webhook events with signature verification.
        Integrates with Slack, Email, and Jira for notifications and ticket creation.
        """
        try:
            # Verify webhook signature
            if not self._verify_webhook_signature(event_data, signature):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature",
                )

            event = ZoomWebhookEvent(**event_data)
            logger.info(f"Processing Zoom webhook event: {event.event}")

            if event.event == "meeting.started":
                meeting_id = event.payload.get("object", {}).get("id")
                topic = event.payload.get("object", {}).get("topic", "Untitled Meeting")
                await self.slack.send_message(
                    channel="#meetings",
                    text=f"Zoom meeting started: {topic} (ID: {meeting_id})",
                )
                await self.jira.create_ticket(
                    summary=f"Zoom Meeting Started: {topic}",
                    description=f"Meeting ID: {meeting_id}\nEvent: {event.event}",
                    project_key="MEET",
                )

            elif event.event == "meeting.ended":
                meeting_id = event.payload.get("object", {}).get("id")
                topic = event.payload.get("object", {}).get("topic", "Untitled Meeting")
                await self.slack.send_message(
                    channel="#meetings",
                    text=f"Zoom meeting ended: {topic} (ID: {meeting_id})",
                )
                await self.email.send_email(
                    to_email=settings.ADMIN_EMAIL,
                    subject=f"Zoom Meeting Ended: {topic}",
                    body=f"The Zoom meeting {topic} (ID: {meeting_id}) has ended.",
                )

        except Exception as e:
            logger.error(f"Error processing Zoom webhook: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process Zoom webhook event",
            )

    def _verify_webhook_signature(self, event_data: Dict[str, Any], signature: str) -> bool:
        """
        Verify the authenticity of the Zoom webhook event using HMAC SHA-256.
        """
        try:
            # Extract timestamp and signature from the provided signature header
            parts = signature.split(",")
            timestamp = next((p.split("=")[1] for p in parts if "v0" in p), "")
            provided_hash = next((p.split("=")[1] for p in parts if "v1" in p), "")

            # Construct the message to hash
            message = f"v0:{timestamp}:{json.dumps(event_data, separators=(',', ':'))}"
            computed_hash = hmac.new(
                self.webhook_secret_token.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(computed_hash, provided_hash)
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {str(e)}")
            return False

    async def get_user_info(self, user: User) -> Dict[str, Any]:
        """
        Fetch user information from Zoom API.
        """
        try:
            if not user.zoom_access_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not authenticated with Zoom",
                )

            headers = self._get_headers(user.zoom_access_token)
            response = requests.get(f"{self.base_url}/users/me", headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch Zoom user info: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch Zoom user information",
            )