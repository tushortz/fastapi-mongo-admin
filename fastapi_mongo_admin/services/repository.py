"""Collection repository for CRUD operations."""

from __future__ import annotations

from typing import Any, Union

from bson import ObjectId
from bson.errors import InvalidId

from fastapi_mongo_admin.admin.model import ModelAdmin
from fastapi_mongo_admin.db.async_backend import AsyncMotorBackend
from fastapi_mongo_admin.db.sync_backend import SyncPyMongoBackend
from fastapi_mongo_admin.exceptions import DocumentNotFoundError
from fastapi_mongo_admin.schemas.forms import parse_form_to_model
from fastapi_mongo_admin.schemas.inference import prepare_for_mongodb, serialize_document
from fastapi_mongo_admin.services.mapping import translate_from_db, translate_to_db
from fastapi_mongo_admin.services.queryset import (
    build_changelist_query,
    parse_ordering,
    resolve_changelist_ordering,
)

Backend = Union[AsyncMotorBackend, SyncPyMongoBackend]


class CollectionRepository:
    """Repository wrapping sync or async MongoDB backend."""

    def __init__(self, backend: Backend, model_admin: ModelAdmin) -> None:
        self.backend = backend
        self.model_admin = model_admin
        self.collection_name = model_admin.collection_name or ""
        self._is_async = isinstance(backend, AsyncMotorBackend)

    def _id_query(self, doc_id: str) -> dict[str, Any]:
        try:
            return {"_id": ObjectId(doc_id)}
        except (InvalidId, TypeError):
            return {"_id": doc_id}

    async def list_documents(
        self,
        *,
        page: int = 1,
        search: str = "",
        filter_params: dict[str, str] | None = None,
        date_hierarchy_params: dict[str, str] | None = None,
        show_all: bool = False,
        request: Any = None,
    ) -> dict[str, Any]:
        """List documents with pagination."""
        per_page = self.model_admin.list_max_show_all if show_all else self.model_admin.list_per_page
        skip = (max(page, 1) - 1) * per_page
        base = self.model_admin.get_queryset(request, {})
        query = build_changelist_query(
            self.model_admin,
            search=search,
            filter_params=filter_params,
            date_hierarchy_params=date_hierarchy_params,
            base_query=base,
        )
        ordering = resolve_changelist_ordering(self.model_admin, filter_params)
        sort = parse_ordering(ordering, self.model_admin.field_mapping)
        if self._is_async:
            total = await self.backend.count(query)  # type: ignore[union-attr]
            docs = await self.backend.find(  # type: ignore[union-attr]
                query, skip=skip, limit=per_page, sort=sort
            )
        else:
            total = self.backend.count(query)  # type: ignore[union-attr]
            docs = self.backend.find(query, skip=skip, limit=per_page, sort=sort)  # type: ignore[union-attr]
        mapping = self.model_admin.field_mapping
        results = [serialize_document(translate_from_db(d, mapping)) for d in docs]
        results = await self._apply_select_related(results)
        return {
            "results": results,
            "total": total,
            "page": page,
            "per_page": per_page,
            "num_pages": max(1, (total + per_page - 1) // per_page),
        }

    async def get_document(self, doc_id: str) -> dict[str, Any]:
        """Fetch single document by id."""
        query = self._id_query(doc_id)
        if self._is_async:
            doc = await self.backend.find_one(query)  # type: ignore[union-attr]
        else:
            doc = self.backend.find_one(query)  # type: ignore[union-attr]
        if not doc:
            raise DocumentNotFoundError(doc_id, self.collection_name)
        return serialize_document(translate_from_db(doc, self.model_admin.field_mapping))

    async def create_document(self, form_data: dict[str, Any], request: Any = None) -> str:
        """Create document from form data."""
        validated = parse_form_to_model(
            self.model_admin.model,
            form_data,
            readonly_fields=self.model_admin.get_readonly_fields(request),
        )
        data = await self.model_admin.save_model(request, {}, validated, is_new=True)
        db_doc = prepare_for_mongodb(translate_to_db(data, self.model_admin.field_mapping))
        if self._is_async:
            return await self.backend.insert_one(db_doc)  # type: ignore[union-attr]
        return self.backend.insert_one(db_doc)  # type: ignore[union-attr]

    async def update_document(self, doc_id: str, form_data: dict[str, Any], request: Any = None) -> bool:
        """Update document from form data."""
        existing = await self.get_document(doc_id)
        validated = parse_form_to_model(
            self.model_admin.model,
            form_data,
            existing=existing,
            readonly_fields=self.model_admin.get_readonly_fields(request, existing),
        )
        data = await self.model_admin.save_model(request, existing, validated, is_new=False)
        db_doc = prepare_for_mongodb(translate_to_db(data, self.model_admin.field_mapping))
        query = self._id_query(doc_id)
        if self._is_async:
            return await self.backend.update_one(query, db_doc)  # type: ignore[union-attr]
        return self.backend.update_one(query, db_doc)  # type: ignore[union-attr]

    async def delete_document(self, doc_id: str, request: Any = None) -> bool:
        """Delete document by id."""
        doc = await self.get_document(doc_id)
        await self.model_admin.delete_model(request, doc)
        query = self._id_query(doc_id)
        if self._is_async:
            return await self.backend.delete_one(query)  # type: ignore[union-attr]
        return self.backend.delete_one(query)  # type: ignore[union-attr]

    async def delete_many(self, doc_ids: list[str]) -> int:
        """Bulk delete by ids."""
        oids = []
        for doc_id in doc_ids:
            try:
                oids.append(ObjectId(doc_id))
            except (InvalidId, TypeError):
                oids.append(doc_id)
        query: dict[str, Any] = {"_id": {"$in": oids}}
        if self._is_async:
            return await self.backend.delete_many(query)  # type: ignore[union-attr]
        return self.backend.delete_many(query)  # type: ignore[union-attr]

    async def _apply_select_related(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Batch-fetch related documents for list_select_related."""
        related = self.model_admin.list_select_related
        if not related or not results:
            return results
        for field_name, related_collection in related.items():
            ids = [r.get(field_name) for r in results if r.get(field_name)]
            if not ids:
                continue
            related_backend = getattr(self, "_related_backends", {}).get(related_collection)
            if related_backend is None:
                continue
            if self._is_async:
                related_docs = await related_backend.find_by_ids(ids)  # type: ignore[union-attr]
            else:
                related_docs = related_backend.find_by_ids(ids)  # type: ignore[union-attr]
            lookup = {str(d.get("_id")): d for d in related_docs}
            for row in results:
                ref_id = row.get(field_name)
                if ref_id is not None:
                    row[f"_{field_name}_related"] = lookup.get(str(ref_id))
        return results

    def set_related_backend(self, collection: str, backend: Backend) -> None:
        """Register backend for list_select_related lookups."""
        if not hasattr(self, "_related_backends"):
            self._related_backends: dict[str, Backend] = {}
        self._related_backends[collection] = backend
