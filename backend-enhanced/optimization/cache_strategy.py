# backend-enhanced/optimization/cache_strategy.py
"""
Advanced caching strategy implementation for optimizing database access,
API responses, and static content delivery. Integrates with CDN, load balancing,
and auto-scaling mechanisms to ensure high performance and reliability.

This module provides a multi-layer caching approach using Redis for in-memory caching,
filesystem caching for static assets, and CDN integration for global content delivery.
"""

import json
import logging
import time
from typing import Any, Dict, Optional, Union
from functools import wraps
import redis
from django.core.cache import cache
from django.conf import settings
import hashlib
import os
from pathlib import Path
import boto3
from botocore.exceptions import ClientError

# Configure logging for monitoring cache operations and errors
logger = logging.getLogger(__name__)

# Redis client initialization with connection pooling and error handling
try:
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
        decode_responses=True,
        socket_timeout=5,
        retry_on_timeout=True
    )
    redis_client.ping()  # Test connection on initialization
    logger.info("Redis connection established successfully")
except redis.ConnectionError as e:
    logger.error(f"Failed to connect to Redis: {str(e)}")
    redis_client = None

# AWS CloudFront client for CDN integration
try:
    cloudfront_client = boto3.client(
        'cloudfront',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION
    )
    logger.info("CloudFront client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize CloudFront client: {str(e)}")
    cloudfront_client = None


class CacheStrategy:
    """
    A comprehensive caching strategy class that implements multiple caching layers
    including in-memory (Redis), filesystem, and CDN caching.
    """
    
    def __init__(self, default_ttl: int = 3600) -> None:
        """
        Initialize the cache strategy with default TTL and configuration.
        
        Args:
            default_ttl (int): Default time-to-live for cached items in seconds.
        """
        self.default_ttl = default_ttl
        self.filesystem_cache_dir = Path(settings.CACHE_DIR) / "filesystem"
        self.filesystem_cache_dir.mkdir(parents=True, exist_ok=True)

    def generate_cache_key(self, prefix: str, *args: Any) -> str:
        """
        Generate a unique cache key based on prefix and arguments.
        Uses SHA-256 hashing to ensure consistent key length and uniqueness.
        
        Args:
            prefix (str): Cache key prefix for namespace.
            *args: Variable arguments to include in the key.
            
        Returns:
            str: Unique cache key.
        """
        key_parts = [str(arg) for arg in args]
        key_string = f"{prefix}:{':'.join(key_parts)}"
        return hashlib.sha256(key_string.encode()).hexdigest()

    def get_from_redis(self, key: str) -> Optional[Any]:
        """
        Retrieve data from Redis cache with error handling.
        
        Args:
            key (str): Cache key to lookup.
            
        Returns:
            Optional[Any]: Cached data if found, None otherwise.
        """
        if not redis_client:
            logger.warning("Redis client not available")
            return None
            
        try:
            data = redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except redis.RedisError as e:
            logger.error(f"Redis get error for key {key}: {str(e)}")
            return None

    def set_to_redis(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Store data in Redis cache with error handling.
        
        Args:
            key (str): Cache key to store under.
            value (Any): Data to cache.
            ttl (Optional[int]): Time-to-live in seconds, defaults to class TTL.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if not redis_client:
            logger.warning("Redis client not available")
            return False
            
        try:
            serialized_value = json.dumps(value)
            redis_client.setex(
                key,
                ttl or self.default_ttl,
                serialized_value
            )
            logger.debug(f"Successfully cached data in Redis for key: {key}")
            return True
        except redis.RedisError as e:
            logger.error(f"Redis set error for key {key}: {str(e)}")
            return False

    def get_from_filesystem(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve data from filesystem cache.
        
        Args:
            key (str): Cache key to lookup.
            
        Returns:
            Optional[Dict[str, Any]]: Cached data if found and not expired, None otherwise.
        """
        file_path = self.filesystem_cache_dir / key
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if data.get('expires_at', 0) > time.time():
                        return data.get('value')
                    else:
                        file_path.unlink()  # Remove expired cache
                        logger.debug(f"Removed expired filesystem cache for key: {key}")
            return None
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Filesystem cache read error for key {key}: {str(e)}")
            return None

    def set_to_filesystem(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Store data in filesystem cache with expiration.
        
        Args:
            key (str): Cache key to store under.
            value (Any): Data to cache.
            ttl (Optional[int]): Time-to-live in seconds.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        file_path = self.filesystem_cache_dir / key
        try:
            data = {
                'value': value,
                'expires_at': time.time() + (ttl or self.default_ttl)
            }
            with open(file_path, 'w') as f:
                json.dump(data, f)
            logger.debug(f"Successfully cached data in filesystem for key: {key}")
            return True
        except IOError as e:
            logger.error(f"Filesystem cache write error for key {key}: {str(e)}")
            return False

    def invalidate_cdn_cache(self, paths: list[str]) -> bool:
        """
        Invalidate CDN cache for specified paths.
        
        Args:
            paths (list[str]): List of paths to invalidate in CloudFront.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if not cloudfront_client:
            logger.warning("CloudFront client not available")
            return False
            
        try:
            response = cloudfront_client.create_invalidation(
                DistributionId=settings.CLOUDFRONT_DISTRIBUTION_ID,
                InvalidationBatch={
                    'Paths': {
                        'Quantity': len(paths),
                        'Items': paths
                    },
                    'CallerReference': str(time.time())
                }
            )
            logger.info(f"CDN cache invalidated for paths: {paths}")
            return True
        except ClientError as e:
            logger.error(f"CloudFront invalidation error: {str(e)}")
            return False

    def cache_decorator(self, prefix: str, ttl: Optional[int] = None):
        """
        Decorator for caching function results in multiple layers.
        First checks Redis, then filesystem, then executes function if no cache hit.
        
        Args:
            prefix (str): Cache key prefix for namespace.
            ttl (Optional[int]): Custom TTL for this cache entry.
            
        Returns:
            Callable: Decorated function with caching.
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                cache_key = self.generate_cache_key(prefix, *args, **kwargs)
                
                # Try Redis first (fastest)
                cached_result = self.get_from_redis(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit in Redis for key: {cache_key}")
                    return cached_result
                    
                # Try filesystem cache next
                cached_result = self.get_from_filesystem(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit in filesystem for key: {cache_key}")
                    # Update Redis with filesystem cache hit for faster future access
                    self.set_to_redis(cache_key, cached_result, ttl)
                    return cached_result
                    
                # Cache miss - execute the function
                result = await func(*args, **kwargs)
                
                # Store result in both Redis and filesystem
                self.set_to_redis(cache_key, result, ttl)
                self.set_to_filesystem(cache_key, result, ttl)
                logger.debug(f"Cache miss - stored result for key: {cache_key}")
                
                return result
            return wrapper
        return decorator


# Singleton instance for global access
cache_strategy = CacheStrategy()