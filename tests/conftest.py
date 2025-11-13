"""Pytest configuration and fixtures."""

from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from fastapi_mongo_admin.services import CollectionService

# Mock data for tests
MOCK_DOCUMENTS = [
    {"_id": ObjectId(), "name": "Test 1", "value": 10, "active": True},
    {"_id": ObjectId(), "name": "Test 2", "value": 20, "active": False},
    {"_id": ObjectId(), "name": "Test 3", "value": 30, "active": True},
]


class MockCursor:
    """Mock cursor that supports method chaining."""

    def __init__(self, documents, query=None):
        self.documents = documents.copy()
        self.query = query or {}
        self._sort_spec = None
        self._limit_val = None
        self._skip_val = None

        # Apply query filter
        if query:
            if "active" in query:
                self.documents = [d for d in self.documents if d.get("active") == query["active"]]
            if "_id" in query:
                if isinstance(query["_id"], dict):
                    if "$in" in query["_id"]:
                        ids = [
                            ObjectId(id_str) if isinstance(id_str, str) else id_str
                            for id_str in query["_id"]["$in"]
                        ]
                        self.documents = [d for d in self.documents if d["_id"] in ids]
                    elif "$gt" in query["_id"]:
                        self.documents = [
                            d for d in self.documents if d["_id"] > query["_id"]["$gt"]
                        ]
                    elif "$lt" in query["_id"]:
                        self.documents = [
                            d for d in self.documents if d["_id"] < query["_id"]["$lt"]
                        ]
                else:
                    self.documents = [d for d in self.documents if d["_id"] == query["_id"]]

    def sort(self, sort_spec):
        """Chainable sort method."""
        self._sort_spec = sort_spec
        if sort_spec:
            # sort_spec is a list of tuples like [("field", 1)]
            if isinstance(sort_spec, list) and len(sort_spec) > 0:
                sort_key, sort_dir = sort_spec[0]
                # Handle None values by treating them as smaller than any value
                def sort_key_func(x):
                    val = x.get(sort_key)
                    if val is None:
                        return (0, None)  # Tuple to handle comparison
                    return (1, val)

                self.documents.sort(key=sort_key_func, reverse=(sort_dir == -1))
        return self

    def limit(self, limit_val):
        """Chainable limit method."""
        self._limit_val = limit_val
        return self

    def skip(self, skip_val):
        """Chainable skip method."""
        self._skip_val = skip_val
        return self

    def __aiter__(self):
        """Async iterator."""

        async def async_iter():
            # Apply sort if set
            if self._sort_spec:
                if isinstance(self._sort_spec, list) and len(self._sort_spec) > 0:
                    sort_key, sort_dir = self._sort_spec[0]
                    self.documents.sort(key=lambda x: x.get(sort_key, 0), reverse=(sort_dir == -1))

            # Apply skip
            docs = self.documents
            if self._skip_val:
                docs = docs[self._skip_val :]

            # Apply limit
            if self._limit_val:
                docs = docs[: self._limit_val]

            for doc in docs:
                yield doc

        return async_iter()

    async def to_list(self, length=None):
        """Convert cursor to list."""
        result = []
        async for doc in self:
            result.append(doc)
            if length and len(result) >= length:
                break
        return result


@pytest_asyncio.fixture
async def mock_collection():
    """Create a mocked MongoDB collection."""
    collection = AsyncMock()

    # Mock find() operations - returns a chainable cursor
    def mock_find(query=None, projection=None):
        # Handle empty collection case (when query is specifically for empty)
        if query == {"_empty": True}:
            return MockCursor([], query)
        return MockCursor(MOCK_DOCUMENTS, query)

    collection.find = MagicMock(side_effect=mock_find)

    # Mock aggregate() operations
    def mock_aggregate(pipeline):
        # Simple aggregation mock - return facet result
        filtered_docs = MOCK_DOCUMENTS.copy()
        total_count = len(MOCK_DOCUMENTS)

        # Filter based on $match stages
        for stage in pipeline:
            if "$match" in stage:
                query = stage["$match"]
                if "active" in query:
                    filtered_docs = [d for d in filtered_docs if d.get("active") == query["active"]]
                    total_count = len(filtered_docs)
                # Handle text search with $or (should match documents containing the text)
                if "$or" in query:
                    # For text search, check if any field contains the search term
                    or_conditions = query["$or"]
                    search_terms = []
                    for condition in or_conditions:
                        for field, regex in condition.items():
                            if isinstance(regex, dict) and "$regex" in regex:
                                search_terms.append(regex["$regex"])

                    if search_terms:
                        # Filter documents that contain any search term
                        matched_docs = []
                        for doc in filtered_docs:
                            doc_str = str(doc.values())
                            if any(term in doc_str for term in search_terms):
                                matched_docs.append(doc)
                        filtered_docs = matched_docs
                        total_count = len(filtered_docs)
                # Handle queries that don't match any documents
                if "nonexistent" in query:
                    filtered_docs = []
                    total_count = 0

        # Apply $sort if present
        for stage in pipeline:
            if "$sort" in stage:
                sort_spec = stage["$sort"]
                sort_key = list(sort_spec.keys())[0] if isinstance(sort_spec, dict) else "_id"
                sort_dir = sort_spec[sort_key] if isinstance(sort_spec, dict) else 1
                filtered_docs.sort(key=lambda x: x.get(sort_key, 0), reverse=(sort_dir == -1))

        # Apply $skip and $limit from $facet
        skip = 0
        limit = len(filtered_docs)
        for stage in pipeline:
            if "$facet" in stage:
                facet = stage["$facet"]
                if "data" in facet:
                    for op in facet["data"]:
                        if "$skip" in op:
                            skip = op["$skip"]
                        if "$limit" in op:
                            limit = op["$limit"]

        # Apply skip and limit
        result_docs = filtered_docs[skip : skip + limit]

        # Handle $project if present
        for stage in pipeline:
            if "$project" in stage:
                project_fields = stage["$project"]
                if isinstance(project_fields, dict):
                    projected_docs = []
                    for doc in result_docs:
                        projected_doc = {}
                        for field, include in project_fields.items():
                            if include:
                                if field in doc:
                                    projected_doc[field] = doc[field]
                        projected_docs.append(projected_doc)
                    result_docs = projected_docs

        result = {
            "data": result_docs,
            "total": [{"count": total_count}],
        }

        # Mock async iteration
        cursor = MagicMock()

        async def async_iter(self):
            yield result

        cursor.__aiter__ = async_iter
        cursor.to_list = AsyncMock(return_value=[result])
        return cursor

    collection.aggregate = MagicMock(side_effect=mock_aggregate)

    # Mock insert_many()
    def mock_insert_many(documents):
        if not documents or len(documents) == 0:
            raise ValueError("documents must be a non-empty list")
        mock_result = MagicMock()
        mock_result.inserted_ids = [ObjectId() for _ in documents]
        return mock_result

    collection.insert_many = AsyncMock(side_effect=mock_insert_many)

    # Mock update_one()
    mock_update_result = MagicMock()
    mock_update_result.modified_count = 1
    collection.update_one = AsyncMock(return_value=mock_update_result)

    # Mock delete_one()
    mock_delete_result = MagicMock()
    mock_delete_result.deleted_count = 1
    collection.delete_one = AsyncMock(return_value=mock_delete_result)

    # Mock bulk_write()
    def mock_bulk_write(operations):
        mock_result = MagicMock()
        # Count delete and replace operations
        delete_count = sum(1 for op in operations if hasattr(op, "filter"))
        replace_count = sum(1 for op in operations if hasattr(op, "replacement"))
        mock_result.modified_count = replace_count
        mock_result.deleted_count = delete_count
        return mock_result

    collection.bulk_write = AsyncMock(side_effect=mock_bulk_write)

    # Mock delete_many() for bulk delete
    async def mock_delete_many(filter_dict):
        # Count matching documents
        count = 0
        if "_id" in filter_dict:
            if "$in" in filter_dict["_id"]:
                # Convert string IDs to ObjectIds for comparison
                ids = []
                for id_str in filter_dict["_id"]["$in"]:
                    try:
                        ids.append(ObjectId(id_str) if isinstance(id_str, str) else id_str)
                    except (ValueError, TypeError):
                        pass
                count = len([d for d in MOCK_DOCUMENTS if d["_id"] in ids])
        mock_result = MagicMock()
        mock_result.deleted_count = count
        return mock_result

    collection.delete_many = AsyncMock(side_effect=mock_delete_many)

    # Mock count_documents()
    collection.count_documents = AsyncMock(return_value=len(MOCK_DOCUMENTS))

    # Mock drop()
    collection.drop = AsyncMock()

    return collection


@pytest_asyncio.fixture
async def mock_database(mock_collection):
    """Create a mocked MongoDB database."""
    database = AsyncMock()

    # Mock collection access
    def get_collection(name):
        return mock_collection

    database.__getitem__ = MagicMock(side_effect=get_collection)
    database.get_collection = AsyncMock(return_value=mock_collection)
    database.list_collection_names = AsyncMock(return_value=["test_collection"])

    # Mock drop_database()
    database.client = MagicMock()
    database.client.drop_database = AsyncMock()

    return database


@pytest_asyncio.fixture
async def mock_client(mock_database):
    """Create a mocked MongoDB client."""
    client = AsyncMock()

    # Mock database access
    def get_database(name):
        return mock_database

    client.__getitem__ = MagicMock(side_effect=get_database)
    client.get_database = AsyncMock(return_value=mock_database)
    client.close = AsyncMock()

    return client


@pytest_asyncio.fixture
async def test_client(mock_client):
    """Create a test MongoDB client (mocked)."""
    return mock_client


@pytest_asyncio.fixture
async def test_database(mock_database):
    """Create a test database (mocked)."""
    return mock_database


@pytest_asyncio.fixture
async def test_collection(mock_collection):
    """Create a test collection with sample data (mocked)."""
    return mock_collection


@pytest_asyncio.fixture
async def collection_service(mock_database):
    """Create a collection service instance (mocked)."""
    return CollectionService(mock_database)
