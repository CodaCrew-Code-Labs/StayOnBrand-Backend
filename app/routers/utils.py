"""
Utility endpoints for health checks and supported formats.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.config import Settings, get_settings
from app.dependencies import get_optional_user, get_redis
from app.models.common import HealthResponse, User
from app.models.responses import SupportedFormat, SupportedFormatsResponse
from app.services.redis_service import RedisService

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Utilities"],
    responses={
        500: {"description": "Internal Server Error"},
    },
)


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="""
    Check the health status of the API and its dependencies.

    This endpoint returns the current status of the API including:
    - Overall health status
    - API version
    - Environment name
    - Status of key dependencies (Redis, etc.)

    Use this endpoint for monitoring and load balancer health checks.
    """,
    responses={
        200: {
            "description": "API is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "API is healthy",
                        "status": "healthy",
                        "version": "1.0.0",
                        "environment": "development",
                        "dependencies": {
                            "redis": "healthy",
                        },
                    }
                }
            },
        },
    },
)
async def health_check(
    settings: Annotated[Settings, Depends(get_settings)],
    redis: Annotated[RedisService, Depends(get_redis)],
) -> HealthResponse:
    """
    Check API health status.

    Args:
        settings: Application settings.
        redis: Redis service for checking connection.

    Returns:
        HealthResponse with health status and dependency checks.
    """
    # TODO: Implement comprehensive health checks
    # - Check Redis connection
    # - Check any other critical dependencies
    # - Return aggregated health status

    dependencies = {}

    # Check Redis
    try:
        redis_healthy = await redis.health_check()
        dependencies["redis"] = "healthy" if redis_healthy else "unhealthy"
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        dependencies["redis"] = "unhealthy"

    # Determine overall status
    all_healthy = all(status == "healthy" for status in dependencies.values())
    overall_status = "healthy" if all_healthy else "degraded"

    return HealthResponse(
        success=True,
        message=f"API is {overall_status}",
        status=overall_status,
        version=settings.app_version,
        environment=settings.environment,
        dependencies=dependencies,
    )


@router.get(
    "/utils/supported-formats",
    response_model=SupportedFormatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get supported file formats",
    description="""
    Get information about supported file formats and upload limits.

    This endpoint returns details about:
    - Supported image file formats and extensions
    - Allowed MIME types
    - Maximum file size limits
    - Maximum image dimensions

    Use this information to validate files before upload.
    """,
    responses={
        200: {
            "description": "Supported formats retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Supported formats retrieved",
                        "image_formats": [
                            {
                                "extension": "jpg",
                                "mime_type": "image/jpeg",
                                "max_size_mb": 10,
                                "description": "JPEG image format",
                            },
                            {
                                "extension": "png",
                                "mime_type": "image/png",
                                "max_size_mb": 10,
                                "description": "PNG image format",
                            },
                        ],
                        "max_file_size_mb": 10,
                        "max_dimensions": {
                            "width": 4096,
                            "height": 4096,
                        },
                    }
                }
            },
        },
    },
)
async def get_supported_formats(
    settings: Annotated[Settings, Depends(get_settings)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> SupportedFormatsResponse:
    """
    Get supported file formats and limits.

    Args:
        settings: Application settings.
        current_user: Optional authenticated user.

    Returns:
        SupportedFormatsResponse with format details.
    """
    # TODO: Implement format information retrieval
    # - Build list of supported formats
    # - Include MIME types and descriptions
    # - Return size limits

    # Format descriptions
    format_descriptions = {
        "jpg": "JPEG image format - lossy compression, good for photos",
        "jpeg": "JPEG image format - lossy compression, good for photos",
        "png": "PNG image format - lossless compression, supports transparency",
        "gif": "GIF image format - supports animation, limited colors",
        "webp": "WebP image format - modern format with good compression",
        "svg": "SVG vector format - scalable, XML-based",
    }

    # MIME type mapping
    mime_mapping = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "svg": "image/svg+xml",
    }

    image_formats = []
    for ext in settings.allowed_image_extensions:
        ext_lower = ext.lower()
        image_formats.append(
            SupportedFormat(
                extension=ext_lower,
                mime_type=mime_mapping.get(ext_lower, f"image/{ext_lower}"),
                max_size_mb=settings.max_file_size_mb,
                description=format_descriptions.get(ext_lower, f"{ext.upper()} image format"),
            )
        )

    return SupportedFormatsResponse(
        success=True,
        message="Supported formats retrieved",
        image_formats=image_formats,
        max_file_size_mb=settings.max_file_size_mb,
        max_dimensions={
            "width": 4096,  # TODO: Make configurable
            "height": 4096,
        },
    )
