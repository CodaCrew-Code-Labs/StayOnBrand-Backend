"""
FastAPI dependency injection providers.
"""

import logging

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings, get_settings
from app.models.common import User
from app.services.auth_service import AuthenticationError, AuthService, get_auth_service
from app.services.brand_service import BrandService, get_brand_service
from app.services.color_service import ColorService, get_color_service
from app.services.redis_service import RedisService, get_redis_service
from app.services.storage_service import StorageService, get_storage_service
from app.services.validation_service import ValidationService, get_validation_service
from app.services.wcag_service import WCAGService, get_wcag_service

logger = logging.getLogger(__name__)

# Security scheme
bearer_scheme = HTTPBearer(auto_error=False)


async def get_settings_dep() -> Settings:
    """Dependency to get application settings."""
    return get_settings()


async def get_redis(settings: Settings = Depends(get_settings_dep)) -> RedisService:
    """
    Dependency to get Redis service.

    Args:
        settings: Application settings.

    Returns:
        RedisService instance.
    """
    return await get_redis_service()


async def get_auth(settings: Settings = Depends(get_settings_dep)) -> AuthService:
    """
    Dependency to get auth service.

    Args:
        settings: Application settings.

    Returns:
        AuthService instance.
    """
    return get_auth_service()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth),
) -> User:
    """
    Dependency to get the current authenticated user.

    Extracts and verifies JWT token from Authorization header.

    Args:
        credentials: Bearer token credentials.
        auth_service: Auth service for verification.

    Returns:
        Authenticated User object.

    Raises:
        HTTPException: If authentication fails.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "MISSING_TOKEN",
                "message": "Authentication token is required",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = await auth_service.verify_token(credentials.credentials)
        return user
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": e.code,
                "message": e.message,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth),
) -> User | None:
    """
    Dependency to optionally get the current user.

    Returns None if no token is provided instead of raising an error.

    Args:
        credentials: Bearer token credentials.
        auth_service: Auth service for verification.

    Returns:
        Authenticated User object or None.
    """
    if not credentials:
        return None

    try:
        return await auth_service.verify_token(credentials.credentials)
    except AuthenticationError:
        return None


def require_permission(permission: str):
    """
    Dependency factory to require a specific permission.

    Args:
        permission: The required permission.

    Returns:
        Dependency function.

    Example:
        @router.get("/admin")
        async def admin_endpoint(
            user: User = Depends(require_permission("admin:read"))
        ):
            ...
    """

    async def permission_checker(
        current_user: User = Depends(get_current_user),
        auth_service: AuthService = Depends(get_auth),
    ) -> User:
        if not auth_service.has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "INSUFFICIENT_PERMISSIONS",
                    "message": f"Permission '{permission}' is required",
                },
            )
        return current_user

    return permission_checker


def require_role(role: str):
    """
    Dependency factory to require a specific role.

    Args:
        role: The required role.

    Returns:
        Dependency function.

    Example:
        @router.get("/admin")
        async def admin_endpoint(
            user: User = Depends(require_role("admin"))
        ):
            ...
    """

    async def role_checker(
        current_user: User = Depends(get_current_user),
        auth_service: AuthService = Depends(get_auth),
    ) -> User:
        if not auth_service.has_role(current_user, role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "INSUFFICIENT_ROLE",
                    "message": f"Role '{role}' is required",
                },
            )
        return current_user

    return role_checker


async def get_color_service_dep() -> ColorService:
    """Dependency to get color service."""
    return get_color_service()


async def get_brand_service_dep(
    redis: RedisService = Depends(get_redis),
) -> BrandService:
    """
    Dependency to get brand service.

    Args:
        redis: Redis service for caching.

    Returns:
        BrandService instance.
    """
    return get_brand_service(redis)


async def get_wcag_service_dep(
    color_service: ColorService = Depends(get_color_service_dep),
    redis: RedisService = Depends(get_redis),
) -> WCAGService:
    """
    Dependency to get WCAG service.

    Args:
        color_service: Color service for contrast calculations.
        redis: Redis service for caching.

    Returns:
        WCAGService instance.
    """
    return get_wcag_service(color_service, redis)


async def get_validation_service_dep(
    redis: RedisService = Depends(get_redis),
) -> ValidationService:
    """
    Dependency to get validation service.

    Args:
        redis: Redis service for storage.

    Returns:
        ValidationService instance.
    """
    return get_validation_service(redis)


async def get_storage_service_dep(
    redis: RedisService = Depends(get_redis),
) -> StorageService:
    """
    Dependency to get storage service.

    Args:
        redis: Redis service for metadata storage.

    Returns:
        StorageService instance.
    """
    return get_storage_service(redis)


async def verify_api_key(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    settings: Settings = Depends(get_settings_dep),
) -> bool:
    """
    Dependency to verify API key for service-to-service auth.

    Args:
        x_api_key: API key from header.
        settings: Application settings.

    Returns:
        True if API key is valid.

    Raises:
        HTTPException: If API key is invalid or missing.
    """
    # TODO: Implement API key verification
    # - Check against configured API keys
    # - Support multiple keys for different services
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "MISSING_API_KEY",
                "message": "API key is required",
            },
        )

    # TODO: Verify against stored API keys
    # For now, always return True (placeholder)
    return True
