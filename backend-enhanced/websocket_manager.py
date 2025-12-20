"""
WebSocket manager for real-time collaboration
Handles presence, live updates, and collaborative editing
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set, Optional
import json
import logging
import asyncio
from datetime import datetime
from collections import defaultdict
import uuid

from redis_client import redis_client

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections for real-time features"""

    def __init__(self):
        # Active connections: {meeting_id: {user_id: WebSocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = defaultdict(dict)

        # User metadata: {connection_id: {user_id, meeting_id, username, etc.}}
        self.connection_metadata: Dict[str, Dict] = {}

        # Heartbeat tracking
        self.last_heartbeat: Dict[str, datetime] = {}

    async def connect(
        self,
        websocket: WebSocket,
        meeting_id: str,
        user_id: str,
        username: str = "Anonymous"
    ):
        """
        Accept WebSocket connection and register user
        """
        await websocket.accept()

        connection_id = str(uuid.uuid4())

        # Store connection
        self.active_connections[meeting_id][user_id] = websocket

        # Store metadata
        self.connection_metadata[connection_id] = {
            "user_id": user_id,
            "meeting_id": meeting_id,
            "username": username,
            "connected_at": datetime.utcnow().isoformat(),
            "connection_id": connection_id
        }

        # Update last heartbeat
        self.last_heartbeat[connection_id] = datetime.utcnow()

        # Add to Redis presence
        await redis_client.add_user_to_meeting(
            meeting_id,
            user_id,
            {
                "username": username,
                "connected_at": datetime.utcnow().isoformat(),
                "connection_id": connection_id
            }
        )

        # Notify others
        await self.broadcast_to_meeting(
            meeting_id,
            {
                "type": "user_joined",
                "user_id": user_id,
                "username": username,
                "timestamp": datetime.utcnow().isoformat()
            },
            exclude_user=user_id
        )

        # Send current presence to new user
        users = await redis_client.get_meeting_users(meeting_id)
        await self.send_personal_message(
            websocket,
            {
                "type": "presence_update",
                "users": users,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        logger.info(f"✅ User {username} ({user_id}) joined meeting {meeting_id}")

        return connection_id

    async def disconnect(self, connection_id: str):
        """
        Disconnect user and clean up
        """
        if connection_id not in self.connection_metadata:
            return

        metadata = self.connection_metadata[connection_id]
        user_id = metadata["user_id"]
        meeting_id = metadata["meeting_id"]
        username = metadata["username"]

        # Remove from active connections
        if meeting_id in self.active_connections:
            if user_id in self.active_connections[meeting_id]:
                del self.active_connections[meeting_id][user_id]

            # Clean up empty meetings
            if not self.active_connections[meeting_id]:
                del self.active_connections[meeting_id]

        # Remove metadata
        del self.connection_metadata[connection_id]

        # Remove heartbeat tracking
        if connection_id in self.last_heartbeat:
            del self.last_heartbeat[connection_id]

        # Remove from Redis presence
        await redis_client.remove_user_from_meeting(meeting_id, user_id)

        # Notify others
        await self.broadcast_to_meeting(
            meeting_id,
            {
                "type": "user_left",
                "user_id": user_id,
                "username": username,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        logger.info(f"👋 User {username} ({user_id}) left meeting {meeting_id}")

    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """Send message to specific WebSocket connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")

    async def broadcast_to_meeting(
        self,
        meeting_id: str,
        message: dict,
        exclude_user: Optional[str] = None
    ):
        """
        Broadcast message to all users in a meeting
        """
        if meeting_id not in self.active_connections:
            return

        disconnected = []

        for user_id, websocket in self.active_connections[meeting_id].items():
            if exclude_user and user_id == exclude_user:
                continue

            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to user {user_id}: {e}")
                disconnected.append(user_id)

        # Clean up disconnected users
        for user_id in disconnected:
            if user_id in self.active_connections[meeting_id]:
                del self.active_connections[meeting_id][user_id]

    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all connected users"""
        for meeting_id in list(self.active_connections.keys()):
            await self.broadcast_to_meeting(meeting_id, message)

    async def handle_message(
        self,
        connection_id: str,
        message_data: dict
    ):
        """
        Handle incoming WebSocket messages
        """
        if connection_id not in self.connection_metadata:
            return

        metadata = self.connection_metadata[connection_id]
        meeting_id = metadata["meeting_id"]
        user_id = metadata["user_id"]
        username = metadata["username"]

        message_type = message_data.get("type")

        # Handle different message types
        if message_type == "heartbeat":
            await self.handle_heartbeat(connection_id)

        elif message_type == "cursor_position":
            await self.handle_cursor_position(
                meeting_id,
                user_id,
                username,
                message_data.get("data", {})
            )

        elif message_type == "edit":
            await self.handle_edit(
                meeting_id,
                user_id,
                username,
                message_data.get("data", {})
            )

        elif message_type == "typing":
            await self.handle_typing(
                meeting_id,
                user_id,
                username,
                message_data.get("data", {})
            )

        elif message_type == "reaction":
            await self.handle_reaction(
                meeting_id,
                user_id,
                username,
                message_data.get("data", {})
            )

        else:
            logger.warning(f"Unknown message type: {message_type}")

    async def handle_heartbeat(self, connection_id: str):
        """Update heartbeat timestamp"""
        self.last_heartbeat[connection_id] = datetime.utcnow()

    async def handle_cursor_position(
        self,
        meeting_id: str,
        user_id: str,
        username: str,
        data: dict
    ):
        """Broadcast cursor position to other users"""
        await self.broadcast_to_meeting(
            meeting_id,
            {
                "type": "cursor_position",
                "user_id": user_id,
                "username": username,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            },
            exclude_user=user_id
        )

    async def handle_edit(
        self,
        meeting_id: str,
        user_id: str,
        username: str,
        data: dict
    ):
        """Handle real-time editing"""
        # Broadcast edit to others
        await self.broadcast_to_meeting(
            meeting_id,
            {
                "type": "edit",
                "user_id": user_id,
                "username": username,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            },
            exclude_user=user_id
        )

        # Invalidate meeting cache since data changed
        await redis_client.invalidate_meeting_cache(meeting_id)

    async def handle_typing(
        self,
        meeting_id: str,
        user_id: str,
        username: str,
        data: dict
    ):
        """Handle typing indicators"""
        await self.broadcast_to_meeting(
            meeting_id,
            {
                "type": "typing",
                "user_id": user_id,
                "username": username,
                "is_typing": data.get("is_typing", False),
                "field": data.get("field"),
                "timestamp": datetime.utcnow().isoformat()
            },
            exclude_user=user_id
        )

    async def handle_reaction(
        self,
        meeting_id: str,
        user_id: str,
        username: str,
        data: dict
    ):
        """Handle reactions/emojis"""
        await self.broadcast_to_meeting(
            meeting_id,
            {
                "type": "reaction",
                "user_id": user_id,
                "username": username,
                "emoji": data.get("emoji"),
                "target": data.get("target"),  # What they're reacting to
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    async def get_meeting_presence(self, meeting_id: str) -> List[Dict]:
        """Get list of users currently in a meeting"""
        users = await redis_client.get_meeting_users(meeting_id)
        return [
            {
                "user_id": user_id,
                **user_data
            }
            for user_id, user_data in users.items()
        ]

    async def cleanup_stale_connections(self, timeout_seconds: int = 60):
        """Remove connections that haven't sent heartbeat"""
        now = datetime.utcnow()
        stale_connections = []

        for connection_id, last_heartbeat in self.last_heartbeat.items():
            if (now - last_heartbeat).total_seconds() > timeout_seconds:
                stale_connections.append(connection_id)

        for connection_id in stale_connections:
            await self.disconnect(connection_id)

        if stale_connections:
            logger.info(f"Cleaned up {len(stale_connections)} stale connections")

    async def start_heartbeat_monitor(self):
        """Background task to monitor heartbeats"""
        while True:
            await asyncio.sleep(30)  # Check every 30 seconds
            await self.cleanup_stale_connections(timeout_seconds=60)


# Global connection manager instance
manager = ConnectionManager()


# Background task to monitor heartbeats
async def start_heartbeat_monitor():
    """Start the heartbeat monitoring background task"""
    await manager.start_heartbeat_monitor()
