"""
Redis client for caching, session management, and real-time features
"""
import redis.asyncio as aioredis
import redis
import json
import logging
from typing import Optional, Any, Dict
from datetime import timedelta
from config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client wrapper with connection pooling"""

    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.sync_redis: Optional[redis.Redis] = None

    async def connect(self):
        """Establish Redis connection"""
        try:
            self.redis = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )

            # Test connection
            await self.redis.ping()
            logger.info("✅ Redis connected successfully")

        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.redis = None

    async def disconnect(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")

    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        if not self.redis:
            return None
        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """
        Set value in Redis
        Args:
            key: Redis key
            value: Value to store (will be JSON serialized if dict/list)
            expire: Expiration time in seconds
        """
        if not self.redis:
            return False
        try:
            # Serialize dicts/lists to JSON
            if isinstance(value, (dict, list)):
                value = json.dumps(value)

            if expire:
                await self.redis.setex(key, expire, value)
            else:
                await self.redis.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        if not self.redis:
            return False
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.redis:
            return False
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False

    async def get_json(self, key: str) -> Optional[Dict]:
        """Get JSON value from Redis"""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON for key: {key}")
        return None

    async def set_json(
        self,
        key: str,
        value: Dict,
        expire: Optional[int] = None
    ) -> bool:
        """Set JSON value in Redis"""
        return await self.set(key, json.dumps(value), expire)

    # ========================================================================
    # REAL-TIME FEATURES
    # ========================================================================

    async def publish(self, channel: str, message: Dict) -> int:
        """
        Publish message to Redis pub/sub channel
        Returns number of subscribers that received the message
        """
        if not self.redis:
            return 0
        try:
            return await self.redis.publish(
                channel,
                json.dumps(message)
            )
        except Exception as e:
            logger.error(f"Redis PUBLISH error: {e}")
            return 0

    async def subscribe(self, *channels: str):
        """Subscribe to Redis pub/sub channels"""
        if not self.redis:
            return None
        try:
            pubsub = self.redis.pubsub()
            await pubsub.subscribe(*channels)
            return pubsub
        except Exception as e:
            logger.error(f"Redis SUBSCRIBE error: {e}")
            return None

    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================

    async def set_session(
        self,
        session_id: str,
        data: Dict,
        expire_seconds: int = 3600
    ) -> bool:
        """Store session data"""
        key = f"session:{session_id}"
        return await self.set_json(key, data, expire_seconds)

    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        key = f"session:{session_id}"
        return await self.get_json(key)

    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        key = f"session:{session_id}"
        return await self.delete(key)

    # ========================================================================
    # WEBSOCKET PRESENCE
    # ========================================================================

    async def add_user_to_meeting(
        self,
        meeting_id: str,
        user_id: str,
        user_data: Dict
    ) -> bool:
        """Add user to meeting presence set"""
        key = f"meeting:{meeting_id}:users"
        try:
            await self.redis.hset(key, user_id, json.dumps(user_data))
            await self.redis.expire(key, 7200)  # 2 hours
            return True
        except Exception as e:
            logger.error(f"Redis HSET error: {e}")
            return False

    async def remove_user_from_meeting(
        self,
        meeting_id: str,
        user_id: str
    ) -> bool:
        """Remove user from meeting presence"""
        key = f"meeting:{meeting_id}:users"
        try:
            await self.redis.hdel(key, user_id)
            return True
        except Exception as e:
            logger.error(f"Redis HDEL error: {e}")
            return False

    async def get_meeting_users(self, meeting_id: str) -> Dict[str, Dict]:
        """Get all users in a meeting"""
        key = f"meeting:{meeting_id}:users"
        try:
            users = await self.redis.hgetall(key)
            return {
                user_id: json.loads(data)
                for user_id, data in users.items()
            }
        except Exception as e:
            logger.error(f"Redis HGETALL error: {e}")
            return {}

    # ========================================================================
    # CACHING
    # ========================================================================

    async def cache_meeting(
        self,
        meeting_id: str,
        meeting_data: Dict,
        expire_seconds: int = 300
    ) -> bool:
        """Cache meeting data"""
        key = f"cache:meeting:{meeting_id}"
        return await self.set_json(key, meeting_data, expire_seconds)

    async def get_cached_meeting(self, meeting_id: str) -> Optional[Dict]:
        """Get cached meeting data"""
        key = f"cache:meeting:{meeting_id}"
        return await self.get_json(key)

    async def invalidate_meeting_cache(self, meeting_id: str) -> bool:
        """Invalidate meeting cache"""
        key = f"cache:meeting:{meeting_id}"
        return await self.delete(key)

    # ========================================================================
    # RATE LIMITING
    # ========================================================================

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """
        Check if request is within rate limit
        Returns True if allowed, False if rate limited
        """
        if not self.redis:
            return True  # Allow if Redis unavailable

        try:
            current = await self.redis.incr(f"ratelimit:{key}")
            if current == 1:
                await self.redis.expire(f"ratelimit:{key}", window_seconds)

            return current <= max_requests
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True  # Allow on error

    # ========================================================================
    # HEALTH CHECK
    # ========================================================================

    async def health_check(self) -> bool:
        """Check Redis health"""
        if not self.redis:
            return False
        try:
            await self.redis.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False


# Global Redis client instance
redis_client = RedisClient()


# Dependency for FastAPI
async def get_redis() -> RedisClient:
    """Get Redis client instance"""
    return redis_client
