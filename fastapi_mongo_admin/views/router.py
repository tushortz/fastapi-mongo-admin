"""Admin view routes."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Body, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from jinja2 import Environment, FileSystemLoader, select_autoescape

from fastapi_mongo_admin.admin.actions import DELETE_SELECTED_ACTION, run_delete_selected
from fastapi_mongo_admin.exceptions import ValidationError as AdminValidationError
from fastapi_mongo_admin.services.import_export import (
    FORMAT_MEDIA_TYPES,
    export_documents,
    export_filename,
    normalize_format,
    parse_import_payload,
    sanitize_import_record,
    validate_import_record,
)
from fastapi_mongo_admin.admin.model import ModelAdmin
from fastapi_mongo_admin.admin.site import AdminSite
from fastapi_mongo_admin.db.async_backend import AsyncMotorBackend
from fastapi_mongo_admin.db.sync_backend import SyncPyMongoBackend
from fastapi_mongo_admin.deps import optional_user, require_permission, verify_csrf
from fastapi_mongo_admin.exceptions import (
    AdminException,
    DocumentNotFoundError,
    PermissionDeniedError,
)
from fastapi_mongo_admin.services.repository import CollectionRepository
from fastapi_mongo_admin.views.context import (
    build_bulk_delete_context,
    build_changelist_context,
    build_form_context,
    build_index_context,
)
from fastapi_mongo_admin.views.htmx import is_htmx, render_partial
from fastapi_mongo_admin.views.messages import (
    FLASH_ADDED,
    FLASH_CHANGED,
    clear_flash_cookie,
    redirect_to_changelist,
)
from fastapi_mongo_admin.views.preferences import (
    build_ui_context,
    redirect_with_preferences,
    set_preference_cookies,
)


def _render_page(
    env: Environment,
    request: Request,
    template_name: str,
    ctx: dict[str, Any],
    static_url: str,
    status_code: int = 200,
) -> HTMLResponse | RedirectResponse:
    """Render an admin HTML template after applying preference redirects.

    Args:
        env: Jinja2 environment with admin templates.
        request: Current HTTP request.
        template_name: Template path relative to the template loader.
        ctx: Template context variables.
        static_url: Base URL for static assets.
        status_code: HTTP status for successful renders.

    Returns:
        RedirectResponse when language/theme cookies need syncing, otherwise
        HTMLResponse with the rendered page.
    """
    pref_redirect = redirect_with_preferences(request, "")
    if pref_redirect is not None:
        return pref_redirect
    ctx = {**ctx, "static_url": static_url, "request": request}
    template = env.get_template(template_name)
    return HTMLResponse(template.render(**ctx), status_code=status_code)


def _create_jinja_env(admin_site: AdminSite) -> Environment:
    """Create a Jinja2 environment with admin template override support.

    Args:
        admin_site: Admin site providing optional ``template_dirs`` overrides.

    Returns:
        Configured Jinja2 Environment with HTML autoescaping enabled.
    """
    package_templates = Path(__file__).resolve().parent.parent / "templates"
    search_paths = [str(d) for d in admin_site.template_dirs] + [str(package_templates)]
    return Environment(
        loader=FileSystemLoader(search_paths),
        autoescape=select_autoescape(["html", "xml"]),
    )


def _get_repo(
    db: Any,
    model_admin: ModelAdmin,
    mode: Literal["async", "sync"],
    admin_site: AdminSite,
) -> CollectionRepository:
    """Create a collection repository with optional related backends.

    Args:
        db: MongoDB database handle.
        model_admin: ModelAdmin configuration for the collection.
        mode: Backend mode — ``async`` (Motor) or ``sync`` (PyMongo).
        admin_site: Admin site used when resolving related collections.

    Returns:
        CollectionRepository wired to the primary and related backends.
    """
    collection = model_admin.collection_name or ""
    if mode == "async":
        backend = AsyncMotorBackend(db[collection])
        repo = CollectionRepository(backend, model_admin)
        for field, related_col in (model_admin.list_select_related or {}).items():
            repo.set_related_backend(related_col, AsyncMotorBackend(db[related_col]))
        return repo
    backend = SyncPyMongoBackend(db[collection])
    repo = CollectionRepository(backend, model_admin)
    for field, related_col in (model_admin.list_select_related or {}).items():
        repo.set_related_backend(related_col, SyncPyMongoBackend(db[related_col]))
    return repo


async def _render_changelist_with_import_errors(
    request: Request,
    env: Environment,
    admin_site: AdminSite,
    model_admin: ModelAdmin,
    collection: str,
    prefix: str,
    static_url: str,
    get_db: Callable[..., Any],
    mode: Literal["async", "sync"],
    *,
    errors: list[str],
    data_transfer_open: bool = False,
) -> HTMLResponse:
    """Render the changelist with import errors in the data transfer panel."""
    db = await get_db()
    repo = _get_repo(db, model_admin, mode, admin_site)  # type: ignore[arg-type]
    params = {k: str(v) for k, v in request.query_params.items()}
    dh_params = {
        "year": params.get("year"),
        "month": params.get("month"),
        "day": params.get("day"),
    }
    page = int(params.get("page", "1") or "1")
    page_data = await repo.list_documents(
        page=page,
        search=params.get("q", ""),
        filter_params=params,
        date_hierarchy_params=dh_params,
        show_all=params.get("all") == "1",
        request=request,
    )
    ctx = build_changelist_context(
        request,
        admin_site,
        model_admin,
        collection,
        prefix,
        page_data,
        search=params.get("q", ""),
        filter_params=params,
        import_errors=errors,
        data_transfer_open=data_transfer_open,
    )
    return _render_page(env, request, model_admin.change_list_template, ctx, static_url, 400)


def create_admin_router(
    admin_site: AdminSite,
    get_database: Callable[..., Any],
    *,
    prefix: str = "/admin",
    mode: Literal["async", "sync"] = "async",
    auth_dependency: Callable[..., Any] | None = None,
    permission_dependency: Callable[..., Any] | None = None,
    static_url: str = "/admin/static",
    api_write_methods: bool = False,
) -> APIRouter:
    """Create the admin UI and JSON API router.

    Args:
        admin_site: Registered models and global admin configuration.
        get_database: Callable returning the MongoDB database (sync or async).
        prefix: URL prefix for all admin routes (default ``/admin``).
        mode: MongoDB access mode — ``async`` or ``sync``.
        auth_dependency: Optional FastAPI dependency for authentication.
        permission_dependency: Optional dependency checked on the admin index.
        static_url: URL path prefix for packaged admin static files.
        api_write_methods: When ``True``, expose ``POST``, ``PUT``, ``PATCH``, and
            ``DELETE`` JSON API endpoints in the router and OpenAPI schema.
            When ``False`` (default), only ``GET`` endpoints are registered.

    Returns:
        APIRouter with HTML admin views and ``/api`` JSON routes included.
    """
    router = APIRouter(prefix=prefix, tags=["admin"])
    env = _create_jinja_env(admin_site)
    user_dep = optional_user(auth_dependency)

    async def _get_db() -> Any:
        """Resolve the database handle from the user-provided callable.

        Returns:
            MongoDB database instance (awaited when async).
        """
        result = get_database()
        if hasattr(result, "__await__"):
            return await result
        return result

    @router.post("/preferences/", include_in_schema=False)
    async def set_preferences(
        request: Request,
        lang: str = Form(""),
        theme: str = Form(""),
        next_url: str = Form(""),
    ) -> RedirectResponse:
        """Persist language/theme preferences and redirect back.

        Args:
            request: Current HTTP request.
            lang: Selected language code.
            theme: Selected theme name.
            next_url: Redirect target after saving preferences.

        Returns:
            Redirect response with preference cookies set.
        """
        target = next_url or request.headers.get("referer") or f"{prefix}/"
        response = RedirectResponse(url=target, status_code=303)
        set_preference_cookies(response, lang=lang or None, theme=theme or None)
        return response

    @router.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def admin_index(
        request: Request,
        user: Any = Depends(user_dep),
    ) -> Response:
        """Render the admin index listing registered models.

        Args:
            request: Current HTTP request.
            user: Authenticated user from the auth dependency.

        Returns:
            HTML admin index page.
        """
        if permission_dependency is not None:
            await _resolve_dep(permission_dependency, request, user)
        ctx = build_index_context(admin_site, prefix, request)
        return _render_page(env, request, "admin/index.html", ctx, static_url)

    for collection, model_admin in admin_site.get_registered_models().items():
        _register_model_routes(
            router,
            env,
            admin_site,
            collection,
            model_admin,
            _get_db,
            prefix,
            mode,
            auth_dependency,
            user_dep,
            static_url,
        )

    for view in admin_site._custom_views:
        router.add_api_route(
            view["path"],
            view["endpoint"],
            methods=["GET"],
            include_in_schema=False,
            name=view["name"],
        )

    _register_api_routes(
        router,
        admin_site,
        _get_db,
        mode,
        auth_dependency,
        api_write_methods=api_write_methods,
    )
    return router


async def _resolve_dep(dep: Callable[..., Any], request: Request, user: Any) -> Any:
    """Invoke a dependency, supporting sync and async callables.

    Args:
        dep: Dependency callable (0, 1, or 2 positional parameters).
        request: Current HTTP request.
        user: Authenticated user from the auth dependency.

    Returns:
        Result of the dependency invocation.
    """
    result = dep(request, user) if dep.__code__.co_argcount >= 2 else dep()
    if hasattr(result, "__await__"):
        return await result
    return result


def _register_model_routes(
    router: APIRouter,
    env: Environment,
    admin_site: AdminSite,
    collection: str,
    model_admin: ModelAdmin,
    get_db: Callable[..., Any],
    prefix: str,
    mode: str,
    auth_dependency: Callable[..., Any] | None,
    user_dep: Callable[..., Any],
    static_url: str,
) -> None:
    """Register HTML changelist, form, delete, and bulk-action routes for one model.

    Args:
        router: Parent admin APIRouter.
        env: Jinja2 environment for HTML templates.
        admin_site: Admin site registry.
        collection: MongoDB collection name (URL segment).
        model_admin: Per-model admin configuration.
        get_db: Async callable returning the database handle.
        prefix: Admin URL prefix.
        mode: MongoDB access mode.
        auth_dependency: Optional authentication dependency.
        user_dep: Resolved optional-user dependency for the index view.
        static_url: Static asset URL prefix.

    Returns:
        None. Routes are registered on ``router`` in place.
    """
    view_dep = require_permission(model_admin, "view", auth_dependency)
    add_dep = require_permission(model_admin, "add", auth_dependency)
    change_dep = require_permission(model_admin, "change", auth_dependency)
    delete_dep = require_permission(model_admin, "delete", auth_dependency)

    async def _form_context(form_request: Request, **kwargs: Any) -> dict[str, Any]:
        """Build add/change form context with related-field dropdown choices."""
        db = await get_db()
        repo = _get_repo(db, model_admin, mode, admin_site)  # type: ignore[arg-type]
        related_initial = await repo.get_related_form_initial(kwargs.get("obj"))
        return build_form_context(
            form_request,
            admin_site,
            model_admin,
            collection,
            prefix,
            related_initial=related_initial,
            **kwargs,
        )

    @router.get(f"/{collection}/", response_class=HTMLResponse, include_in_schema=False)
    async def changelist(
        request: Request,
        page: int = 1,
        q: str = "",
        all: str = "",
        user: Any = Depends(view_dep),
    ) -> HTMLResponse:
        """Render the model changelist or an HTMX result partial.

        Args:
            request: Current HTTP request.
            page: Page number for pagination.
            q: Search query string.
            all: When ``"1"``, show all rows up to ``list_max_show_all``.
            user: Authenticated user with view permission.

        Returns:
            Full changelist page or HTMX partial HTML.
        """
        db = await get_db()
        repo = _get_repo(db, model_admin, mode, admin_site)  # type: ignore[arg-type]
        params = {k: str(v) for k, v in request.query_params.items()}
        dh_params = {
            "year": params.get("year"),
            "month": params.get("month"),
            "day": params.get("day"),
        }
        page_data = await repo.list_documents(
            page=page,
            search=q,
            filter_params=params,
            date_hierarchy_params=dh_params,
            show_all=all == "1",
            request=request,
        )
        ctx = build_changelist_context(
            request,
            admin_site,
            model_admin,
            collection,
            prefix,
            page_data,
            search=q,
            filter_params=params,
        )
        pref_redirect = redirect_with_preferences(request, "")
        if pref_redirect is not None:
            return pref_redirect
        ctx["static_url"] = static_url
        if is_htmx(request):
            return render_partial(env, "admin/partials/result_list.html", ctx, request)
        response = _render_page(env, request, model_admin.change_list_template, ctx, static_url)
        if ctx.get("success_message"):
            clear_flash_cookie(response)
        return response

    @router.get(
        f"/{collection}/related-lookup/{{field_name}}/",
        include_in_schema=False,
    )
    async def related_lookup(
        request: Request,
        field_name: str,
        q: str = "",
        user: Any = Depends(view_dep),
    ) -> dict[str, Any]:
        """Return JSON matches for a searchable related form field."""
        _ = user
        db = await get_db()
        repo = _get_repo(db, model_admin, mode, admin_site)  # type: ignore[arg-type]
        matches = await repo.search_related_documents(field_name, q)
        return {"results": [{"value": value, "label": label} for value, label in matches]}

    @router.get(f"/{collection}/add/", response_class=HTMLResponse, include_in_schema=False)
    async def add_view(
        request: Request,
        user: Any = Depends(add_dep),
    ) -> HTMLResponse:
        """Render the add-object form.

        Args:
            request: Current HTTP request.
            user: Authenticated user with add permission.

        Returns:
            HTML add form page.
        """
        ctx = await _form_context(request, is_new=True)
        return _render_page(env, request, model_admin.change_form_template, ctx, static_url)

    @router.post(f"/{collection}/add/", response_class=HTMLResponse, include_in_schema=False)
    async def add_post(
        request: Request,
        user: Any = Depends(add_dep),
        csrfmiddlewaretoken: str = Form(""),
    ) -> HTMLResponse:
        """Create a document from the submitted add form.

        Args:
            request: Current HTTP request with form data.
            user: Authenticated user with add permission.
            csrfmiddlewaretoken: CSRF token from the form.

        Returns:
            Redirect to changelist on success, or the form with errors.
        """
        verify_csrf(request, admin_site, csrfmiddlewaretoken)
        form = dict(await request.form())
        form.pop("csrfmiddlewaretoken", None)
        db = await get_db()
        repo = _get_repo(db, model_admin, mode, admin_site)  # type: ignore[arg-type]
        try:
            doc_id = await repo.create_document(form, request)
            obj = await repo.get_document(doc_id)
            obj_repr = model_admin.object_repr(request, obj)
            return redirect_to_changelist(prefix, collection, FLASH_ADDED, obj_repr)
        except AdminException as exc:
            ctx = await _form_context(request, is_new=True, errors=[str(exc.detail)])
            return _render_page(
                env, request, model_admin.change_form_template, ctx, static_url, exc.status_code
            )

    @router.get(
        f"/{collection}/{{doc_id}}/change/", response_class=HTMLResponse, include_in_schema=False
    )
    async def change_view(
        request: Request,
        doc_id: str,
        user: Any = Depends(change_dep),
    ) -> HTMLResponse:
        """Render the change-object form.

        Args:
            request: Current HTTP request.
            doc_id: Document id to edit.
            user: Authenticated user with change permission.

        Returns:
            HTML change form page.

        Raises:
            HTTPException: 404 when the document does not exist.
        """
        db = await get_db()
        repo = _get_repo(db, model_admin, mode, admin_site)  # type: ignore[arg-type]
        try:
            obj = await repo.get_document(doc_id)
        except DocumentNotFoundError:
            raise HTTPException(status_code=404, detail="Document not found") from None
        ctx = await _form_context(request, obj=obj)
        return _render_page(env, request, model_admin.change_form_template, ctx, static_url)

    @router.post(
        f"/{collection}/{{doc_id}}/change/", response_class=HTMLResponse, include_in_schema=False
    )
    async def change_post(
        request: Request,
        doc_id: str,
        user: Any = Depends(change_dep),
        csrfmiddlewaretoken: str = Form(""),
    ) -> HTMLResponse:
        """Update a document from the submitted change form.

        Args:
            request: Current HTTP request with form data.
            doc_id: Document id to update.
            user: Authenticated user with change permission.
            csrfmiddlewaretoken: CSRF token from the form.

        Returns:
            Redirect to changelist on success, or the form with errors.
        """
        verify_csrf(request, admin_site, csrfmiddlewaretoken)
        form = dict(await request.form())
        form.pop("csrfmiddlewaretoken", None)
        db = await get_db()
        repo = _get_repo(db, model_admin, mode, admin_site)  # type: ignore[arg-type]
        try:
            await repo.update_document(doc_id, form, request)
            obj = await repo.get_document(doc_id)
            obj_repr = model_admin.object_repr(request, obj)
            return redirect_to_changelist(prefix, collection, FLASH_CHANGED, obj_repr)
        except AdminException as exc:
            obj = await repo.get_document(doc_id)
            ctx = await _form_context(request, obj=obj, errors=[str(exc.detail)])
            return _render_page(
                env, request, model_admin.change_form_template, ctx, static_url, exc.status_code
            )

    @router.get(
        f"/{collection}/{{doc_id}}/delete/", response_class=HTMLResponse, include_in_schema=False
    )
    async def delete_view(
        request: Request,
        doc_id: str,
        user: Any = Depends(delete_dep),
    ) -> HTMLResponse:
        """Render the single-object delete confirmation page.

        Args:
            request: Current HTTP request.
            doc_id: Document id to delete.
            user: Authenticated user with delete permission.

        Returns:
            HTML delete confirmation page.

        Raises:
            HTTPException: 404 when the document does not exist.
        """
        db = await get_db()
        repo = _get_repo(db, model_admin, mode, admin_site)  # type: ignore[arg-type]
        try:
            obj = await repo.get_document(doc_id)
        except DocumentNotFoundError:
            raise HTTPException(status_code=404, detail="Document not found") from None
        ctx = {
            "site_header": admin_site.site_header,
            "model_name": model_admin.get_model_name(),
            "collection": collection,
            "prefix": prefix,
            "obj": obj,
            "obj_id": doc_id,
            "csrf_token": admin_site.get_csrf_token(request),
            **build_ui_context(request),
        }
        return _render_page(env, request, model_admin.delete_confirmation_template, ctx, static_url)

    @router.post(f"/{collection}/{{doc_id}}/delete/", include_in_schema=False)
    async def delete_post(
        request: Request,
        doc_id: str,
        user: Any = Depends(delete_dep),
        csrfmiddlewaretoken: str = Form(""),
    ) -> RedirectResponse:
        """Delete a single document after confirmation.

        Args:
            request: Current HTTP request.
            doc_id: Document id to delete.
            user: Authenticated user with delete permission.
            csrfmiddlewaretoken: CSRF token from the form.

        Returns:
            Redirect to the model changelist.
        """
        verify_csrf(request, admin_site, csrfmiddlewaretoken)
        db = await get_db()
        repo = _get_repo(db, model_admin, mode, admin_site)  # type: ignore[arg-type]
        await repo.delete_document(doc_id, request)
        return RedirectResponse(url=f"{prefix}/{collection}/", status_code=303)

    @router.post(f"/{collection}/action/", response_class=Response, include_in_schema=False)
    async def bulk_action(
        request: Request,
        user: Any = Depends(change_dep),
    ) -> Response:
        """Run a bulk admin action or render bulk delete confirmation.

        Args:
            request: Current HTTP request with action form data.
            user: Authenticated user with change permission.

        Returns:
            Redirect, confirmation HTML, or error response.
        """
        form = await request.form()
        verify_csrf(request, admin_site, str(form.get("csrfmiddlewaretoken", "")))
        action = str(form.get("action", ""))
        actions = {name: method for name, method, _ in model_admin.get_actions()}
        if action not in actions:
            raise HTTPException(status_code=400, detail="Invalid action")
        db = await get_db()
        repo = _get_repo(db, model_admin, mode, admin_site)  # type: ignore[arg-type]
        selected = form.getlist("_selected_action")
        if not selected:
            return RedirectResponse(url=f"{prefix}/{collection}/", status_code=303)
        docs: list[dict[str, Any]] = []
        for doc_id in selected:
            try:
                docs.append(await repo.get_document(doc_id))
            except DocumentNotFoundError:
                continue
        if action == DELETE_SELECTED_ACTION:
            if not model_admin.has_delete_permission(request, user):
                raise PermissionDeniedError(model_admin.collection_name or "model", "delete")
            if str(form.get("confirm", "")) != "1":
                ctx = build_bulk_delete_context(
                    request,
                    admin_site,
                    model_admin,
                    collection,
                    prefix,
                    selected_ids=selected,
                    objects=docs,
                )
                return _render_page(
                    env,
                    request,
                    model_admin.delete_selected_confirmation_template,
                    ctx,
                    static_url,
                )
            await run_delete_selected(model_admin, request, repo, docs, selected)
        else:
            method = actions[action]
            result = method(request, docs)
            if hasattr(result, "__await__"):
                await result
        return RedirectResponse(url=f"{prefix}/{collection}/", status_code=303)

    @router.post(f"/{collection}/export/", include_in_schema=False)
    async def export_data(
        request: Request,
        user: Any = Depends(view_dep),
        csrfmiddlewaretoken: str = Form(""),
        format: str = Form("json"),
        scope: str = Form("selected"),
    ) -> Response:
        """Export documents in the requested format."""
        verify_csrf(request, admin_site, csrfmiddlewaretoken)
        form = await request.form()
        db = await get_db()
        repo = _get_repo(db, model_admin, mode, admin_site)  # type: ignore[arg-type]
        docs: list[dict[str, Any]] = []
        if scope == "all":
            params = {k: str(v) for k, v in request.query_params.items()}
            dh_params = {
                "year": params.get("year"),
                "month": params.get("month"),
                "day": params.get("day"),
            }
            page_data = await repo.list_documents(
                page=1,
                search=params.get("q", ""),
                filter_params=params,
                date_hierarchy_params=dh_params,
                show_all=True,
                request=request,
            )
            docs = list(page_data.get("results", []))
        else:
            selected = form.getlist("_selected_action")
            if not selected:
                raise HTTPException(status_code=400, detail="Select at least one row to export.")
            for doc_id in selected:
                try:
                    docs.append(await repo.get_document(doc_id))
                except DocumentNotFoundError:
                    continue
        if not docs:
            raise HTTPException(status_code=400, detail="No documents available to export.")
        try:
            fmt = normalize_format(format)
            payload = export_documents(docs, fmt)
        except AdminValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc.detail)) from exc
        filename = export_filename(collection, fmt)
        media_type = FORMAT_MEDIA_TYPES[fmt]
        return Response(
            content=payload,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @router.post(f"/{collection}/import/", response_class=Response, include_in_schema=False)
    async def import_post(
        request: Request,
        user: Any = Depends(add_dep),
        csrfmiddlewaretoken: str = Form(""),
        format: str = Form("json"),
    ) -> Response:
        """Import documents from an uploaded file."""
        verify_csrf(request, admin_site, csrfmiddlewaretoken)
        form = await request.form()
        upload = form.get("import_file")
        if upload is None or not hasattr(upload, "read"):
            return await _render_changelist_with_import_errors(
                request,
                env,
                admin_site,
                model_admin,
                collection,
                prefix,
                static_url,
                get_db,
                mode,
                errors=["Please choose a file to import."],
                data_transfer_open=True,
            )
        raw = await upload.read()  # type: ignore[union-attr]
        try:
            records = parse_import_payload(raw, format)
        except AdminValidationError as exc:
            return await _render_changelist_with_import_errors(
                request,
                env,
                admin_site,
                model_admin,
                collection,
                prefix,
                static_url,
                get_db,
                mode,
                errors=[str(exc.detail)],
                data_transfer_open=True,
            )
        db = await get_db()
        repo = _get_repo(db, model_admin, mode, admin_site)  # type: ignore[arg-type]
        created = 0
        errors: list[str] = []
        for index, record in enumerate(records, start=1):
            cleaned = sanitize_import_record(record)
            try:
                validated = validate_import_record(model_admin.model, cleaned)
                await repo.create_document(validated, request)
                created += 1
            except AdminValidationError as exc:
                errors.append(f"Row {index}: {exc.detail}")
        if errors and created == 0:
            return await _render_changelist_with_import_errors(
                request,
                env,
                admin_site,
                model_admin,
                collection,
                prefix,
                static_url,
                get_db,
                mode,
                errors=errors,
                data_transfer_open=True,
            )
        target = f"{prefix}/{collection}/"
        if created:
            target = f"{target}?imported={created}"
        return RedirectResponse(url=target, status_code=303)

    for path, handler in model_admin.get_urls():
        router.add_api_route(
            f"/{collection}/{path}",
            handler,
            methods=["GET"],
            include_in_schema=False,
        )


def _register_api_routes(
    router: APIRouter,
    admin_site: AdminSite,
    get_db: Callable[..., Any],
    mode: str,
    auth_dependency: Callable[..., Any] | None,
    *,
    api_write_methods: bool = False,
) -> None:
    """Register JSON API routes under ``/api``.

    By default only ``GET`` list and detail endpoints are registered and included
    in OpenAPI. When ``api_write_methods`` is ``True``, ``POST``, ``PUT``,
    ``PATCH``, and ``DELETE`` handlers are also registered with permission checks.

    Args:
        router: Parent admin APIRouter to attach the API sub-router to.
        admin_site: Admin site registry for model lookup and related backends.
        get_db: Async callable returning the database handle.
        mode: MongoDB access mode — ``async`` or ``sync``.
        auth_dependency: Optional authentication dependency for permission checks.
        api_write_methods: Enable write JSON API routes and OpenAPI documentation.

    Returns:
        None. Routes are registered on ``router`` in place.
    """
    api = APIRouter(prefix="/api", tags=["admin-api"])

    def _make_list_handler(coll: str, admin: ModelAdmin) -> Callable[..., Any]:
        """Build a paginated list handler for one collection.

        Args:
            coll: Collection URL segment.
            admin: ModelAdmin for the collection.

        Returns:
            Async route handler for ``GET /api/{collection}/``.
        """
        list_dep = require_permission(admin, "view", auth_dependency)

        async def list_api(
            request: Request,
            page: int = 1,
            q: str = "",
            user: Any = Depends(list_dep),
        ) -> dict[str, Any]:
            """Return a paginated JSON list of documents.

            Args:
                request: Current HTTP request.
                page: Page number (1-based).
                q: Search query string.
                user: Authenticated user with view permission.

            Returns:
                Paginated list response dict.
            """
            db = await get_db()
            repo = _get_repo(db, admin, mode, admin_site)  # type: ignore[arg-type]
            return await repo.list_documents(page=page, search=q, request=request)

        list_api.__name__ = f"list_api_{coll}"
        return list_api

    def _make_detail_handler(coll: str, admin: ModelAdmin) -> Callable[..., Any]:
        """Build a single-document GET handler for one collection.

        Args:
            coll: Collection URL segment.
            admin: ModelAdmin for the collection.

        Returns:
            Async route handler for ``GET /api/{collection}/{doc_id}``.
        """
        detail_dep = require_permission(admin, "view", auth_dependency)

        async def detail_api(
            request: Request,
            doc_id: str,
            user: Any = Depends(detail_dep),
        ) -> dict[str, Any]:
            """Return a single document as JSON.

            Args:
                request: Current HTTP request.
                doc_id: Document id string.
                user: Authenticated user with view permission.

            Returns:
                Serialized document dict.
            """
            db = await get_db()
            repo = _get_repo(db, admin, mode, admin_site)  # type: ignore[arg-type]
            return await repo.get_document(doc_id)

        detail_api.__name__ = f"detail_api_{coll}"
        return detail_api

    def _make_create_handler(coll: str, admin: ModelAdmin) -> Callable[..., Any]:
        """Build a document creation handler (``POST``) for one collection.

        Args:
            coll: Collection URL segment.
            admin: ModelAdmin for the collection.

        Returns:
            Async route handler for ``POST /api/{collection}/``.
        """
        add_dep = require_permission(admin, "add", auth_dependency)

        async def create_api(
            request: Request,
            payload: dict[str, Any] = Body(...),
            user: Any = Depends(add_dep),
        ) -> dict[str, Any]:
            """Create a document from a JSON payload.

            Args:
                request: Current HTTP request.
                payload: Document field values.
                user: Authenticated user with add permission.

            Returns:
                Created serialized document dict.
            """
            db = await get_db()
            repo = _get_repo(db, admin, mode, admin_site)  # type: ignore[arg-type]
            doc_id = await repo.create_document(payload, request)
            return await repo.get_document(doc_id)

        create_api.__name__ = f"create_api_{coll}"
        return create_api

    def _make_update_handler(coll: str, admin: ModelAdmin, *, partial: bool) -> Callable[..., Any]:
        """Build a document update handler (``PUT`` or ``PATCH``) for one collection.

        Args:
            coll: Collection URL segment.
            admin: ModelAdmin for the collection.
            partial: Whether this is a PATCH (partial) handler.

        Returns:
            Async route handler for document update.
        """
        change_dep = require_permission(admin, "change", auth_dependency)
        suffix = "patch" if partial else "put"

        async def update_api(
            request: Request,
            doc_id: str,
            payload: dict[str, Any] = Body(...),
            user: Any = Depends(change_dep),
        ) -> dict[str, Any]:
            """Update a document from a JSON payload.

            Args:
                request: Current HTTP request.
                doc_id: Document id string.
                payload: Field values to update.
                user: Authenticated user with change permission.

            Returns:
                Updated serialized document dict.
            """
            db = await get_db()
            repo = _get_repo(db, admin, mode, admin_site)  # type: ignore[arg-type]
            await repo.update_document(doc_id, payload, request)
            return await repo.get_document(doc_id)

        update_api.__name__ = f"{suffix}_api_{coll}"
        return update_api

    def _make_delete_handler(coll: str, admin: ModelAdmin) -> Callable[..., Any]:
        """Build a document delete handler (``DELETE``) for one collection.

        Args:
            coll: Collection URL segment.
            admin: ModelAdmin for the collection.

        Returns:
            Async route handler for ``DELETE /api/{collection}/{doc_id}``.
        """
        delete_dep = require_permission(admin, "delete", auth_dependency)

        async def delete_api(
            request: Request,
            doc_id: str,
            user: Any = Depends(delete_dep),
        ) -> Response:
            """Delete a document by id.

            Args:
                request: Current HTTP request.
                doc_id: Document id string.
                user: Authenticated user with delete permission.

            Returns:
                Empty response with status 204.
            """
            db = await get_db()
            repo = _get_repo(db, admin, mode, admin_site)  # type: ignore[arg-type]
            await repo.delete_document(doc_id, request)
            return Response(status_code=204)

        delete_api.__name__ = f"delete_api_{coll}"
        return delete_api

    for collection, model_admin in admin_site.get_registered_models().items():
        if model_admin.model is None:
            continue
        api.add_api_route(
            f"/{collection}/",
            _make_list_handler(collection, model_admin),
            methods=["GET"],
            include_in_schema=True,
        )
        api.add_api_route(
            f"/{collection}/{{doc_id}}",
            _make_detail_handler(collection, model_admin),
            methods=["GET"],
            include_in_schema=True,
        )
        if api_write_methods:
            api.add_api_route(
                f"/{collection}/",
                _make_create_handler(collection, model_admin),
                methods=["POST"],
                status_code=201,
                include_in_schema=True,
            )
            api.add_api_route(
                f"/{collection}/{{doc_id}}",
                _make_update_handler(collection, model_admin, partial=False),
                methods=["PUT"],
                include_in_schema=True,
            )
            api.add_api_route(
                f"/{collection}/{{doc_id}}",
                _make_update_handler(collection, model_admin, partial=True),
                methods=["PATCH"],
                include_in_schema=True,
            )
            api.add_api_route(
                f"/{collection}/{{doc_id}}",
                _make_delete_handler(collection, model_admin),
                methods=["DELETE"],
                include_in_schema=True,
            )

    router.include_router(api)
