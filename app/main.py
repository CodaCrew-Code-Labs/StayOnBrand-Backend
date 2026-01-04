"""
StayOnBoard Validation API - Main Application Entry Point

This is the main FastAPI application for the StayOnBoard validation API,
providing endpoints for brand validation, WCAG accessibility checking,
and color contrast analysis.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import get_settings
from app.middleware.error_handler import ErrorHandlerMiddleware, setup_exception_handlers
from app.routers import (
    brand_router,
    colors_router,
    utils_router,
    validate_router,
    wcag_router,
)
from app.services.redis_service import close_redis_service, get_redis_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events for the application.
    """
    # Startup
    logger.info("Starting StayOnBoard API...")
    settings = get_settings()

    # Initialize Redis connection
    try:
        await get_redis_service()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}")
        # Continue without Redis - some features may be degraded

    logger.info(
        f"StayOnBoard API v{settings.app_version} started in {settings.environment} mode"
    )

    yield

    # Shutdown
    logger.info("Shutting down StayOnBoard API...")
    await close_redis_service()
    logger.info("StayOnBoard API shutdown complete")


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()

    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        description="""
# StayOnBoard Validation API

A comprehensive API for brand and accessibility validation services.

## Features

- **Color Contrast Analysis**: Check color contrast ratios for WCAG compliance
- **Brand Validation**: Validate images against brand guidelines
- **WCAG Validation**: Check images and designs for accessibility compliance
- **Validation History**: Track and rerun past validations

## Authentication

All endpoints (except health check) require JWT authentication.
Include your token in the Authorization header:

```
Authorization: Bearer <your-token>
```

## Rate Limiting

API requests are rate limited to prevent abuse. Current limits are displayed
in response headers.
        """,
        version=settings.app_version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else "/api/openapi.json",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Add error handling middleware
    app.add_middleware(ErrorHandlerMiddleware)

    # Setup exception handlers
    setup_exception_handlers(app)

    # Include routers
    api_prefix = "/api/v1"

    app.include_router(utils_router, prefix=api_prefix)
    app.include_router(colors_router, prefix=api_prefix)
    app.include_router(brand_router, prefix=api_prefix)
    app.include_router(wcag_router, prefix=api_prefix)
    app.include_router(validate_router, prefix=api_prefix)

    return app


# Create the application instance
app = create_application()


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint redirect to docs."""
    settings = get_settings()
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else None,
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
