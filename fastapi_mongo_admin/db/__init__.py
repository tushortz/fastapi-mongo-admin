"""Database backends."""

from fastapi_mongo_admin.db.async_backend import AsyncMotorBackend
from fastapi_mongo_admin.db.sync_backend import SyncPyMongoBackend

__all__ = ["AsyncMotorBackend", "SyncPyMongoBackend"]
