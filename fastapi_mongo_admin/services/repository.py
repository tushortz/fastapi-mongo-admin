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
    build_related_search_query,
    parse_ordering,
    resolve_changelist_ordering,
)

RELATED_LOOKUP_MIN_CHARS = 2
RELATED_LOOKUP_LIMIT = 25

Backend = Union[AsyncMotorBackend, SyncPyMongoBackend]


def related_object_label(doc: dict[str, Any]) -> str:
    """Return a human-readable label for a related document.

    Args:
        doc: Related MongoDB document.

    Returns:
        Best-effort display label for select widgets and changelists.
    """
    for key in ("name", "title", "slug", "order_number", "code"):
        value = doc.get(key)
        if value not in (None, ""):
            return str(value)
    first = doc.get("first_name", "")
    last = doc.get("last_name", "")
    full_name = f"{first} {last}".strip()
    if full_name:
        return full_name
    email = doc.get("email")
    if email not in (None, ""):
        return str(email)
    doc_id = doc.get("_id")
    return str(doc_id) if doc_id is not None else ""


class CollectionRepository:
    """Repository wrapping sync or async MongoDB backends for one collection."""

    def __init__(self, backend: Backend, model_admin: ModelAdmin) -> None:
        """Initialize the repository.

        Args:
            backend: Sync or async collection backend.
            model_admin: ModelAdmin configuration for validation and hooks.
        """
        self.backend = backend
        self.model_admin = model_admin
        self.collection_name = model_admin.collection_name or ""
        self._is_async = isinstance(backend, AsyncMotorBackend)

    def _id_query(self, doc_id: str) -> dict[str, Any]:
        """Build a MongoDB ``_id`` query from a string id.

        Args:
            doc_id: Document id string.

        Returns:
            Query dict with ``ObjectId`` or raw id value.
        """
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
        """List documents with pagination, search, and filters.

        Args:
            page: Page number (1-based).
            search: Changelist search string.
            filter_params: Active list-filter query parameters.
            date_hierarchy_params: Optional date hierarchy drill-down params.
            show_all: When ``True``, use ``list_max_show_all`` as page size.
            request: Current request passed to queryset hooks.

        Returns:
            Dict with ``results``, ``total``, ``page``, ``per_page``, and
            ``num_pages`` keys.
        """
        per_page = (
            self.model_admin.list_max_show_all if show_all else self.model_admin.list_per_page
        )
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
        """Fetch a single serialized document by id.

        Args:
            doc_id: Document id string.

        Returns:
            Serialized document dict with an ``id`` field.

        Raises:
            DocumentNotFoundError: When no document matches the id.
        """
        query = self._id_query(doc_id)
        if self._is_async:
            doc = await self.backend.find_one(query)  # type: ignore[union-attr]
        else:
            doc = self.backend.find_one(query)  # type: ignore[union-attr]
        if not doc:
            raise DocumentNotFoundError(doc_id, self.collection_name)
        return serialize_document(translate_from_db(doc, self.model_admin.field_mapping))

    async def create_document(self, form_data: dict[str, Any], request: Any = None) -> str:
        """Create a document from form or JSON data.

        Args:
            form_data: Raw field values to validate and persist.
            request: Current request passed to hooks.

        Returns:
            New document id string.
        """
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

    async def update_document(
        self, doc_id: str, form_data: dict[str, Any], request: Any = None
    ) -> bool:
        """Update a document from form or JSON data.

        Args:
            doc_id: Document id string.
            form_data: Raw field values to validate and persist.
            request: Current request passed to hooks.

        Returns:
            ``True`` when the backend reports a successful update.
        """
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
        """Delete a document by id.

        Args:
            doc_id: Document id string.
            request: Current request passed to ``delete_model`` hook.

        Returns:
            ``True`` when the backend reports a successful delete.
        """
        doc = await self.get_document(doc_id)
        await self.model_admin.delete_model(request, doc)
        query = self._id_query(doc_id)
        if self._is_async:
            return await self.backend.delete_one(query)  # type: ignore[union-attr]
        return self.backend.delete_one(query)  # type: ignore[union-attr]

    async def delete_many(self, doc_ids: list[str]) -> int:
        """Bulk delete documents by id.

        Args:
            doc_ids: Document id strings.

        Returns:
            Number of deleted documents.
        """
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

    async def get_related_form_initial(
        self, obj: dict[str, Any] | None
    ) -> dict[str, tuple[str, str]]:
        """Fetch the current value label for ``list_select_related`` form fields.

        Args:
            obj: Existing document on change forms.

        Returns:
            Mapping of field name to ``(value, label)`` for the selected reference.
        """
        related = self.model_admin.list_select_related
        if not related or not obj:
            return {}
        admin_choices = self.model_admin.choices or {}
        result: dict[str, tuple[str, str]] = {}
        for field_name, related_collection in related.items():
            if field_name in admin_choices:
                continue
            ref_id = obj.get(field_name)
            if ref_id in (None, ""):
                continue
            related_backend = getattr(self, "_related_backends", {}).get(related_collection)
            if related_backend is None:
                continue
            if self._is_async:
                docs = await related_backend.find_by_ids([ref_id])  # type: ignore[union-attr]
            else:
                docs = related_backend.find_by_ids([ref_id])  # type: ignore[union-attr]
            if docs:
                doc = docs[0]
                result[field_name] = (str(doc["_id"]), related_object_label(doc))
        return result

    async def search_related_documents(
        self,
        field_name: str,
        query: str,
        *,
        min_chars: int = RELATED_LOOKUP_MIN_CHARS,
        limit: int = RELATED_LOOKUP_LIMIT,
    ) -> list[tuple[str, str]]:
        """Search related documents for a searchable form dropdown.

        Args:
            field_name: Model field configured in ``list_select_related``.
            query: User search string.
            min_chars: Minimum query length before searching.
            limit: Maximum number of matches to return.

        Returns:
            List of ``(value, label)`` tuples sorted by label.
        """
        related = self.model_admin.list_select_related
        if not related or field_name not in related:
            return []
        if len(query.strip()) < min_chars:
            return []
        related_collection = related[field_name]
        related_backend = getattr(self, "_related_backends", {}).get(related_collection)
        if related_backend is None:
            return []
        search_query = build_related_search_query(query.strip())
        if not search_query:
            return []
        if self._is_async:
            docs = await related_backend.find(search_query, limit=limit)  # type: ignore[union-attr]
        else:
            docs = related_backend.find(search_query, limit=limit)  # type: ignore[union-attr]
        choices = [(str(doc["_id"]), related_object_label(doc)) for doc in docs if doc.get("_id")]
        choices.sort(key=lambda item: item[1].lower())
        return choices

    async def _apply_select_related(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Batch-fetch related documents for ``list_select_related``.

        Args:
            results: Changelist result rows.

        Returns:
            Rows enriched with ``_{field}_related`` lookup data.
        """
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
        """Register a backend for ``list_select_related`` lookups.

        Args:
            collection: Related collection name.
            backend: Backend for that collection.

        Returns:
            None.
        """
        if not hasattr(self, "_related_backends"):
            self._related_backends: dict[str, Backend] = {}
        self._related_backends[collection] = backend
