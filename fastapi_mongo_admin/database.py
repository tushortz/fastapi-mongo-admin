"""Database connection utilities with optimized pooling."""

from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient


def create_optimized_client(
    connection_string: str,
    max_pool_size: int = 50,
    min_pool_size: int = 10,
    max_idle_time_ms: int = 45000,
    **kwargs: Any,
) -> AsyncIOMotorClient:
    """Create MongoDB client with optimized connection pooling.

    Args:
        connection_string: MongoDB connection string
        max_pool_size: Maximum number of connections in the pool (default: 50)
        min_pool_size: Minimum number of connections in the pool (default: 10)
        max_idle_time_ms: Maximum time a connection can be idle before being closed (default: 45000)
        **kwargs: Additional arguments passed to AsyncIOMotorClient

    Returns:
        Configured AsyncIOMotorClient instance

    Example:
        ```python
        from fastapi_mongo_admin.database import create_optimized_client

        client = create_optimized_client(
            "mongodb://localhost:27017",
            max_pool_size=100,
            min_pool_size=20
        )
        database = client["my_database"]
        ```
    """
    return AsyncIOMotorClient(
        connection_string,
        maxPoolSize=max_pool_size,
        minPoolSize=min_pool_size,
        maxIdleTimeMS=max_idle_time_ms,
        **kwargs,
    )
