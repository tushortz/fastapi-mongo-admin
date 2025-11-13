"""Tests for database utilities."""

import pytest

from fastapi_mongo_admin.database import create_optimized_client


def test_create_optimized_client_defaults():
    """Test creating optimized client with default parameters."""
    client = create_optimized_client("mongodb://localhost:27017")

    assert client is not None
    # Check that client has the expected attributes
    assert hasattr(client, "max_pool_size") or hasattr(client, "_options")


def test_create_optimized_client_custom_pool():
    """Test creating optimized client with custom pool settings."""
    client = create_optimized_client(
        "mongodb://localhost:27017",
        max_pool_size=100,
        min_pool_size=20,
        max_idle_time_ms=60000,
    )

    assert client is not None


def test_create_optimized_client_with_kwargs():
    """Test creating optimized client with additional kwargs."""
    client = create_optimized_client(
        "mongodb://localhost:27017",
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
    )

    assert client is not None


def test_create_optimized_client_connection_string():
    """Test creating optimized client with different connection strings."""
    # Test with authentication
    client1 = create_optimized_client(
        "mongodb://user:pass@localhost:27017/admin"
    )

    assert client1 is not None

    # Test with replica set
    client2 = create_optimized_client(
        "mongodb://localhost:27017,localhost:27018/?replicaSet=rs0"
    )

    assert client2 is not None

