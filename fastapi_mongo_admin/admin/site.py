"""AdminSite registry."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any, Type

from fastapi import Request
from pydantic import BaseModel

from fastapi_mongo_admin.admin.model import ModelAdmin


class AdminSite:
    """Registry for models and custom admin views."""

    site_header: str = "FastAPI Mongo Admin"
    site_title: str = "Admin"
    index_title: str = "Site administration"

    def __init__(self, name: str = "admin", template_dirs: list[Path] | None = None) -> None:
        self.name = name
        self.template_dirs: list[Path] = list(template_dirs or [])
        self._registry: dict[str, ModelAdmin] = {}
        self._custom_views: list[dict[str, Any]] = []

    def register(
        self,
        model_or_iterable: Type[BaseModel] | Iterable[Type[BaseModel]],
        admin_class: type[ModelAdmin] | None = None,
        **options: Any,
    ) -> None:
        """Register one or more Pydantic models."""
        if isinstance(model_or_iterable, type) and issubclass(model_or_iterable, BaseModel):
            models: list[Type[BaseModel]] = [model_or_iterable]
        else:
            models = list(model_or_iterable)

        for model in models:
            collection_name = options.get("collection_name")
            if admin_class is not None:
                admin_obj = admin_class(model)
                if not collection_name:
                    collection_name = admin_obj.collection_name
            else:
                admin_obj = ModelAdmin(model)

            if not collection_name:
                raise ValueError(
                    f"collection_name must be specified for model {model.__name__}"
                )

            for key, value in options.items():
                if hasattr(admin_obj, key) or key in {
                    "list_display",
                    "search_fields",
                    "list_filter",
                    "field_mapping",
                }:
                    setattr(admin_obj, key, value)

            if collection_name in self._registry:
                raise ValueError(f"Model with collection_name '{collection_name}' is already registered")

            self._registry[collection_name] = admin_obj

    def register_view(
        self,
        name: str,
        path: str,
        endpoint: Callable[..., Any],
        *,
        permission: Callable[[Request, Any], bool] | None = None,
    ) -> None:
        """Register a custom admin page."""
        self._custom_views.append(
            {"name": name, "path": path, "endpoint": endpoint, "permission": permission}
        )

    def get_model_admin(self, collection_name: str) -> ModelAdmin | None:
        """Return ModelAdmin for a collection."""
        return self._registry.get(collection_name)

    def get_registered_collections(self) -> list[str]:
        """Return registered collection names."""
        return list(self._registry.keys())

    def get_registered_models(self) -> dict[str, ModelAdmin]:
        """Return full registry."""
        return dict(self._registry)

    def get_csrf_token(self, request: Request) -> str:
        """Return CSRF token from session when SessionMiddleware is enabled."""
        if "session" not in request.scope:
            return ""
        token = request.session.get("csrf_token")
        return str(token) if token else ""


site = AdminSite()
