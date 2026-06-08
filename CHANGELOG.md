# Changelog

## [2.0.0] - 2026-06-08

### Breaking Changes

- Removed React SPA and `/admin-ui` mount; admin is server-rendered at `/admin`
- Removed `MongoAdmin` alias, `mount_admin_ui`, legacy document API routes
- Removed built-in in-memory token authentication
- Requires Python >= 3.10
- Package management migrated to `uv` / `hatchling`

### Added

- Django-admin-style server-rendered UI (Jinja2 + HTMX)
- Expanded `ModelAdmin`: fieldsets, actions, permissions, `list_select_related`, date hierarchy
- Filter framework: `ChoiceListFilter`, `BooleanFieldListFilter`, `DateFieldListFilter`, `RelatedFieldListFilter`, custom `ListFilter`
- Pluggable `auth_dependency` and `permission_dependency` on `mount_admin_app`
- Sync (`mode="sync"`) and async (`mode="async"`) MongoDB backends
- Template override support via `AdminSite(template_dirs=...)`
- Custom admin views via `site.register_view()`
- JSON API at `/admin/api/{collection}/`
- Comprehensive test suite with `mongomock` and `httpx`

### Migration from v0.2.x

1. Remove separate UI mount — use `mount_admin_app` only
2. Replace client-side API usage with HTML admin or `/admin/api/` endpoints
3. Wire `auth_dependency` for secured deployments
4. Update `list_filter` to use filter classes where needed

## [0.2.1] - Previous release

Registry-based admin with React UI (deprecated in v2).
