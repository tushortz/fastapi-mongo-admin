"""Utility functions for admin module."""

from pathlib import Path

from fastapi.staticfiles import StaticFiles


def get_static_directory() -> Path:
    """Get the path to the admin static files directory."""
    return Path(__file__).parent / "static"


def mount_admin_ui(app, mount_path: str = "/admin-ui") -> bool:
    """Mount the admin UI static files to the FastAPI app.

    Args:
        app: FastAPI application instance
        mount_path: Path to mount the admin UI (default: /admin-ui)

    Returns:
        True if successfully mounted, False otherwise
    """
    try:
        static_dir = get_static_directory()
        if static_dir.exists():
            app.mount(mount_path, StaticFiles(directory=str(static_dir), html=True), name="admin-ui")
            return True
        return False
    except Exception:
        return False

