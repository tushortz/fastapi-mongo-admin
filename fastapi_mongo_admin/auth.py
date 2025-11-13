"""Authentication and authorization utilities for admin interface."""

import logging
from typing import Callable, Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

# Simple in-memory token store (for basic auth)
# In production, use proper session management or JWT
_token_store: dict[str, dict] = {}

# Default authentication function (can be overridden)
_auth_function: Optional[Callable[[str], bool]] = None

# Default permission checker (can be overridden)
_permission_checker: Optional[Callable[[str, str, str], bool]] = None

security = HTTPBearer(auto_error=False)


def set_auth_function(auth_func: Callable[[str], bool]) -> None:
    """Set custom authentication function.

    Args:
        auth_func: Function that takes a token and returns True if valid
    """
    global _auth_function
    _auth_function = auth_func


def set_permission_checker(permission_func: Callable[[str, str, str], bool]) -> None:
    """Set custom permission checker.

    Args:
        permission_func: Function that takes (token, collection, action) and returns True if allowed
    """
    global _permission_checker
    _permission_checker = permission_func


def create_token(user_id: str, permissions: Optional[dict] = None) -> str:
    """Create a simple token for authentication.

    Args:
        user_id: User identifier
        permissions: Optional permissions dict

    Returns:
        Token string
    """
    import uuid

    token = str(uuid.uuid4())
    _token_store[token] = {"user_id": user_id, "permissions": permissions or {}}
    return token


def validate_token(token: str) -> bool:
    """Validate a token.

    Args:
        token: Token string

    Returns:
        True if token is valid
    """
    if _auth_function:
        return _auth_function(token)
    return token in _token_store


def check_permission(token: str, collection: str, action: str) -> bool:
    """Check if token has permission for action on collection.

    Args:
        token: Token string
        collection: Collection name
        action: Action (read, write, delete, etc.)

    Returns:
        True if permission is granted
    """
    if _permission_checker:
        return _permission_checker(token, collection, action)

    if token not in _token_store:
        return False

    token_data = _token_store[token]
    permissions = token_data.get("permissions", {})

    # Check collection-specific permissions
    if collection in permissions:
        collection_perms = permissions[collection]
        if isinstance(collection_perms, list):
            return action in collection_perms
        if isinstance(collection_perms, dict):
            return collection_perms.get(action, False)

    # Check global permissions
    if "*" in permissions:
        global_perms = permissions["*"]
        if isinstance(global_perms, list):
            return action in global_perms
        if isinstance(global_perms, dict):
            return global_perms.get(action, False)

    # Default: no permissions
    return False


def get_user_from_token(token: str) -> Optional[dict]:
    """Get user data from token.

    Args:
        token: Token string

    Returns:
        User data dict or None
    """
    return _token_store.get(token)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> Optional[dict]:
    """Dependency to get current user from token.

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        User data dict

    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        # No credentials provided - allow if auth is not required
        if not _auth_function:
            return None  # No auth required
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    if not validate_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_data = get_user_from_token(token)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_data


def require_permission(collection: str, action: str):
    """Dependency factory to require specific permission.

    Args:
        collection: Collection name
        action: Action (read, write, delete, etc.)

    Returns:
        Dependency function
    """

    async def permission_check(
        user: Optional[dict] = Depends(get_current_user),
        credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    ) -> dict:
        if not user and not credentials:
            # No auth required
            return {}

        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        token = credentials.credentials
        if not check_permission(token, collection, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {action} on {collection}",
            )

        return user or {}

    return permission_check
