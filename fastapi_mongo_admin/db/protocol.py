"""Database backend protocols."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class AsyncCollectionBackend(Protocol):
    """Async MongoDB collection operations."""

    async def find(
        self,
        query: dict[str, Any],
        *,
        skip: int = 0,
        limit: int = 100,
        sort: list[tuple[str, int]] | None = None,
        projection: dict[str, int] | None = None,
    ) -> list[dict[str, Any]]: ...

    async def find_one(
        self,
        query: dict[str, Any],
        projection: dict[str, int] | None = None,
    ) -> dict[str, Any] | None: ...

    async def count(self, query: dict[str, Any]) -> int: ...

    async def insert_one(self, document: dict[str, Any]) -> str: ...

    async def update_one(self, query: dict[str, Any], update: dict[str, Any]) -> bool: ...

    async def delete_one(self, query: dict[str, Any]) -> bool: ...

    async def delete_many(self, query: dict[str, Any]) -> int: ...


@runtime_checkable
class SyncCollectionBackend(Protocol):
    """Sync MongoDB collection operations."""

    def find(
        self,
        query: dict[str, Any],
        *,
        skip: int = 0,
        limit: int = 100,
        sort: list[tuple[str, int]] | None = None,
        projection: dict[str, int] | None = None,
    ) -> list[dict[str, Any]]: ...

    def find_one(
        self,
        query: dict[str, Any],
        projection: dict[str, int] | None = None,
    ) -> dict[str, Any] | None: ...

    def count(self, query: dict[str, Any]) -> int: ...

    def insert_one(self, document: dict[str, Any]) -> str: ...

    def update_one(self, query: dict[str, Any], update: dict[str, Any]) -> bool: ...

    def delete_one(self, query: dict[str, Any]) -> bool: ...

    def delete_many(self, query: dict[str, Any]) -> int: ...
