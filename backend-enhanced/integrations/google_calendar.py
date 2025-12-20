# backend-enhanced/integrations/google_calendar.py
"""
Google Calendar Integration Module

This module handles integration with Google Calendar API for creating, updating,
and deleting events. It includes OAuth2 authentication flow, secure credential
management, and error handling for robust operation.

Dependencies:
- google-auth-oauthlib
- google-auth-httplib2
- google-api-python-client
"""

from typing import Dict, List, Optional, Any
import os
import json
import logging
from datetime import datetime, timedelta
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from flask import current_app

# Configure logging
logger = logging.getLogger(__name__)

# Google Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']


class GoogleCalendarIntegration:
    """Handles Google Calendar API interactions with secure credential management."""

    def __init__(self, credentials_path: str, token_path: str):
        """
        Initialize Google Calendar integration with paths to credentials.

        Args:
            credentials_path (str): Path to the client secrets JSON file.
            token_path (str): Path to store/retrieve user token pickle file.
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.creds: Optional[Credentials] = None
        self.service: Any = None
        self._initialize_credentials()

    def _initialize_credentials(self) -> None:
        """
        Initialize or refresh OAuth2 credentials for Google Calendar API.
        Handles token refresh and initial authentication flow.
        """
        try:
            # Check if token file exists and load credentials
            if os.path.exists(self.token_path):
                with open(self.token_path, 'rb') as token:
                    self.creds = pickle.load(token)

            # If credentials are invalid or expired, refresh or re-authenticate
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES)
                    self.creds = flow.run_local_server(port=0)

                # Save the credentials for future use
                with open(self.token_path, 'wb') as token:
                    pickle.dump(self.creds, token)

            # Build the Google Calendar API service
            self.service = build('calendar', 'v3', credentials=self.creds)
        except Exception as e:
            logger.error(f"Error initializing Google Calendar credentials: {str(e)}")
            raise

    def create_event(self, summary: str, start_time: datetime, end_time: datetime,
                    description: str = "", attendees: List[str] = [],
                    calendar_id: str = 'primary') -> Dict[str, Any]:
        """
        Create a new event in Google Calendar.

        Args:
            summary (str): Event title/summary.
            start_time (datetime): Event start time.
            end_time (datetime): Event end time.
            description (str): Event description.
            attendees (List[str]): List of attendee email addresses.
            calendar_id (str): Target calendar ID (default: 'primary').

        Returns:
            Dict[str, Any]: Created event details from API response.

        Raises:
            HttpError: If API request fails.
        """
        try:
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'attendees': [{'email': email} for email in attendees],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 10},
                    ],
                },
            }

            event_result = self.service.events().insert(
                calendarId=calendar_id, body=event, sendUpdates='all'
            ).execute()

            logger.info(f"Created Google Calendar event: {event_result.get('htmlLink')}")
            return event_result
        except HttpError as error:
            logger.error(f"Error creating Google Calendar event: {str(error)}")
            raise Exception(f"Failed to create event: {str(error)}")

    def update_event(self, event_id: str, summary: Optional[str] = None,
                    start_time: Optional[datetime] = None,
                    end_time: Optional[datetime] = None,
                    description: Optional[str] = None,
                    attendees: Optional[List[str]] = None,
                    calendar_id: str = 'primary') -> Dict[str, Any]:
        """
        Update an existing event in Google Calendar.

        Args:
            event_id (str): ID of the event to update.
            summary (Optional[str]): Updated event title.
            start_time (Optional[datetime]): Updated start time.
            end_time (Optional[datetime]): Updated end time.
            description (Optional[str]): Updated description.
            attendees (Optional[List[str]]): Updated list of attendee emails.
            calendar_id (str): Target calendar ID (default: 'primary').

        Returns:
            Dict[str, Any]: Updated event details from API response.
        """
        try:
            event = self.service.events().get(
                calendarId=calendar_id, eventId=event_id
            ).execute()

            if summary:
                event['summary'] = summary
            if description:
                event['description'] = description
            if start_time:
                event['start']['dateTime'] = start_time.isoformat()
            if end_time:
                event['end']['dateTime'] = end_time.isoformat()
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]

            updated_event = self.service.events().update(
                calendarId=calendar_id, eventId=event_id, body=event, sendUpdates='all'
            ).execute()

            logger.info(f"Updated Google Calendar event: {updated_event.get('htmlLink')}")
            return updated_event
        except HttpError as error:
            logger.error(f"Error updating Google Calendar event: {str(error)}")
            raise Exception(f"Failed to update event: {str(error)}")

    def delete_event(self, event_id: str, calendar_id: str = 'primary') -> bool:
        """
        Delete an event from Google Calendar.

        Args:
            event_id (str): ID of the event to delete.
            calendar_id (str): Target calendar ID (default: 'primary').

        Returns:
            bool: True if deletion successful, False otherwise.
        """
        try:
            self.service.events().delete(
                calendarId=calendar_id, eventId=event_id, sendUpdates='all'
            ).execute()
            logger.info(f"Deleted Google Calendar event: {event_id}")
            return True
        except HttpError as error:
            logger.error(f"Error deleting Google Calendar event: {str(error)}")
            return False

    def get_events(self, start_time: datetime, end_time: datetime,
                  calendar_id: str = 'primary', max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve events from Google Calendar within a time range.

        Args:
            start_time (datetime): Start of time range.
            end_time (datetime): End of time range.
            calendar_id (str): Target calendar ID (default: 'primary').
            max_results (int): Maximum number of events to return.

        Returns:
            List[Dict[str, Any]]: List of event details from API response.
        """
        try:
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=start_time.isoformat(),
                timeMax=end_time.isoformat(),
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            logger.info(f"Retrieved {len(events)} events from Google Calendar")
            return events
        except HttpError as error:
            logger.error(f"Error retrieving Google Calendar events: {str(error)}")
            raise Exception(f"Failed to retrieve events: {str(error)}")


def get_google_calendar_service() -> GoogleCalendarIntegration:
    """
    Factory function to create and return a GoogleCalendarIntegration instance.
    Uses Flask app configuration for credential paths.

    Returns:
        GoogleCalendarIntegration: Initialized Google Calendar service instance.
    """
    credentials_path = current_app.config.get('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
    token_path = current_app.config.get('GOOGLE_TOKEN_PATH', 'token.pickle')
    return GoogleCalendarIntegration(credentials_path, token_path)