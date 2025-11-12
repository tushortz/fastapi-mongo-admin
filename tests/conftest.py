"""Pytest configuration and fixtures."""

import pytest
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from fastapi_mongo_admin.services import CollectionService


@pytest.fixture
async def test_client():
    """Create a test MongoDB client."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    yield client
    client.close()


@pytest.fixture
async def test_database(test_client):
    """Create a test database."""
    db = test_client["test_admin_db"]
    yield db
    # Cleanup: drop test database
    await db.client.drop_database("test_admin_db")


@pytest.fixture
async def test_collection(test_database):
    """Create a test collection with sample data."""
    collection = test_database["test_collection"]

    # Insert test documents
    await collection.insert_many([
        {"name": "Test 1", "value": 10, "active": True},
        {"name": "Test 2", "value": 20, "active": False},
        {"name": "Test 3", "value": 30, "active": True},
    ])

    yield collection

    # Cleanup: drop collection
    await collection.drop()


@pytest.fixture
def collection_service(test_database):
    """Create a collection service instance."""
    return CollectionService(test_database)

