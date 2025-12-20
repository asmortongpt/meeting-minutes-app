# backend-enhanced/optimization/db_pool.py
"""
Database Connection Pooling Module

This module implements a secure and optimized database connection pooling system
using asyncpg for PostgreSQL. It includes connection pooling, retry mechanisms,
health checks, and monitoring capabilities for production environments.
"""

import asyncpg
from asyncpg.pool import Pool
from typing import Optional, Dict, Any
import asyncio
import logging
from contextlib import asynccontextmanager
import os
from datetime import datetime

# Configure logging for database operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabasePool:
    """
    Manages a pool of database connections with health checks and retry logic.
    Optimized for high-concurrency environments with monitoring capabilities.
    """
    
    def __init__(
        self,
        dsn: str,
        min_size: int = 5,
        max_size: int = 20,
        max_queries: int = 50000,
        max_inactive_connection_lifetime: float = 300.0,
        retry_attempts: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize the database connection pool with configuration parameters.
        
        Args:
            dsn (str): Database connection string
            min_size (int): Minimum number of connections in pool
            max_size (int): Maximum number of connections in pool
            max_queries (int): Maximum queries per connection before recycling
            max_inactive_connection_lifetime (float): Max inactive time before closing connection
            retry_attempts (int): Number of retry attempts for failed connections
            retry_delay (float): Delay between retry attempts in seconds
        """
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self.max_queries = max_queries
        self.max_inactive_connection_lifetime = max_inactive_connection_lifetime
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.pool: Optional[Pool] = None
        self._health_check_interval = 30.0  # Seconds between health checks
        self._last_health_check: Optional[datetime] = None
        self._is_healthy = False

    async def initialize(self) -> None:
        """
        Initialize the database connection pool with retry logic.
        """
        attempt = 0
        while attempt < self.retry_attempts:
            try:
                self.pool = await asyncpg.create_pool(
                    dsn=self.dsn,
                    min_size=self.min_size,
                    max_size=self.max_size,
                    max_queries=self.max_queries,
                    max_inactive_connection_lifetime=self.max_inactive_connection_lifetime,
                    # Enable SSL if configured in environment
                    ssl=os.getenv("DB_SSL", "prefer")
                )
                logger.info("Database connection pool initialized successfully")
                self._is_healthy = True
                # Start background health check task
                asyncio.create_task(self._health_check_loop())
                return
            except asyncpg.PostgresError as e:
                attempt += 1
                logger.error(f"Failed to initialize database pool (attempt {attempt}/{self.retry_attempts}): {str(e)}")
                if attempt == self.retry_attempts:
                    raise ConnectionError("Failed to initialize database pool after maximum retries")
                await asyncio.sleep(self.retry_delay)

    async def _health_check_loop(self) -> None:
        """
        Background task to periodically check database pool health.
        """
        while True:
            try:
                await self._perform_health_check()
            except Exception as e:
                logger.error(f"Health check loop error: {str(e)}")
            await asyncio.sleep(self._health_check_interval)

    async def _perform_health_check(self) -> None:
        """
        Perform a health check on the database pool by executing a simple query.
        """
        if self.pool is None:
            self._is_healthy = False
            return

        try:
            async with self.pool.acquire() as connection:
                await connection.execute("SELECT 1")
            self._is_healthy = True
            self._last_health_check = datetime.utcnow()
            logger.debug("Database pool health check passed")
        except asyncpg.PostgresError as e:
            self._is_healthy = False
            logger.error(f"Database pool health check failed: {str(e)}")

    @asynccontextmanager
    async def get_connection(self):
        """
        Context manager for acquiring and releasing database connections from the pool.
        """
        if self.pool is None or not self._is_healthy:
            raise ConnectionError("Database pool is not initialized or unhealthy")

        connection = None
        try:
            connection = await self.pool.acquire()
            yield connection
        except asyncpg.PostgresError as e:
            logger.error(f"Database operation error: {str(e)}")
            raise
        finally:
            if connection:
                await self.pool.release(connection)

    async def execute(self, query: str, *args) -> Any:
        """
        Execute a database query with error handling and logging.
        
        Args:
            query (str): SQL query to execute
            *args: Query parameters
            
        Returns:
            Any: Query results
        """
        start_time = datetime.utcnow()
        try:
            async with self.get_connection() as conn:
                result = await conn.execute(query, *args)
                duration = (datetime.utcnow() - start_time).total_seconds()
                logger.debug(f"Query executed in {duration:.3f}s: {query[:100]}...")
                return result
        except asyncpg.PostgresError as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise

    async def fetch(self, query: str, *args) -> list:
        """
        Fetch results from a database query.
        
        Args:
            query (str): SQL query to execute
            *args: Query parameters
            
        Returns:
            list: Query results as list of rows
        """
        start_time = datetime.utcnow()
        try:
            async with self.get_connection() as conn:
                result = await conn.fetch(query, *args)
                duration = (datetime.utcnow() - start_time).total_seconds()
                logger.debug(f"Query fetched in {duration:.3f}s: {query[:100]}...")
                return result
        except asyncpg.PostgresError as e:
            logger.error(f"Query fetch failed: {str(e)}")
            raise

    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """
        Fetch a single row from a database query.
        
        Args:
            query (str): SQL query to execute
            *args: Query parameters
            
        Returns:
            Optional[Dict[str, Any]]: Single row as dictionary or None if no results
        """
        start_time = datetime.utcnow()
        try:
            async with self.get_connection() as conn:
                result = await conn.fetchrow(query, *args)
                duration = (datetime.utcnow() - start_time).total_seconds()
                logger.debug(f"Query fetchrow in {duration:.3f}s: {query[:100]}...")
                return result
        except asyncpg.PostgresError as e:
            logger.error(f"Query fetchrow failed: {str(e)}")
            raise

    async def close(self) -> None:
        """
        Close the database connection pool and release all connections.
        """
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
            self._is_healthy = False
            self.pool = None

    @property
    def is_healthy(self) -> bool:
        """
        Check if the database pool is healthy.
        
        Returns:
            bool: True if pool is healthy, False otherwise
        """
        return self._is_healthy

    @property
    def health_check_timestamp(self) -> Optional[datetime]:
        """
        Get the timestamp of the last health check.
        
        Returns:
            Optional[datetime]: Timestamp of last health check or None if never checked
        """
        return self._last_health_check


# Singleton instance for global access
_db_pool_instance: Optional[DatabasePool] = None


def get_db_pool() -> DatabasePool:
    """
    Get the singleton instance of the database pool.
    
    Returns:
        DatabasePool: The global database pool instance
        
    Raises:
        RuntimeError: If database pool is not initialized
    """
    if _db_pool_instance is None:
        raise RuntimeError("Database pool not initialized")
    return _db_pool_instance


async def init_db_pool(
    dsn: str,
    min_size: int = 5,
    max_size: int = 20,
    max_queries: int = 50000,
    max_inactive_connection_lifetime: float = 300.0
) -> DatabasePool:
    """
    Initialize the global database pool instance.
    
    Args:
        dsn (str): Database connection string
        min_size (int): Minimum number of connections
        max_size (int): Maximum number of connections
        max_queries (int): Maximum queries per connection
        max_inactive_connection_lifetime (float): Max inactive connection lifetime
        
    Returns:
        DatabasePool: Initialized database pool instance
    """
    global _db_pool_instance
    if _db_pool_instance is None:
        _db_pool_instance = DatabasePool(
            dsn=dsn,
            min_size=min_size,
            max_size=max_size,
            max_queries=max_queries,
            max_inactive_connection_lifetime=max_inactive_connection_lifetime
        )
        await _db_pool_instance.initialize()
    return _db_pool_instance


async def close_db_pool() -> None:
    """
    Close the global database pool instance.
    """
    global _db_pool_instance
    if _db_pool_instance is not None:
        await _db_pool_instance.close()
        _db_pool_instance = None