"""
Error handling middleware and exception handlers.
"""

import logging
import traceback
import uuid
from collections.abc import Callable

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.models.common import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware for centralized error handling and request tracking.

    Adds request IDs, logs errors, and ensures consistent error responses.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """
        Process the request and handle any errors.

        Args:
            request: The incoming request.
            call_next: The next middleware/handler in the chain.

        Returns:
            The response from the handler or an error response.
        """
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Add request ID to response headers
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as e:
            # Log the error with request context
            logger.error(
                f"Unhandled error in request {request_id}: {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                },
                exc_info=True,
            )

            # Return error response
            settings = get_settings()
            error_response = ErrorResponse(
                success=False,
                message="An unexpected error occurred",
                request_id=request_id,
                errors=[
                    ErrorDetail(
                        code="INTERNAL_ERROR",
                        message=str(e) if settings.debug else "Internal server error",
                    )
                ],
            )

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response.model_dump(mode="json"),
                headers={"X-Request-ID": request_id},
            )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """
    Handle HTTP exceptions with consistent error format.

    Args:
        request: The incoming request.
        exc: The HTTP exception.

    Returns:
        JSON response with error details.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    error_response = ErrorResponse(
        success=False,
        message=str(exc.detail),
        request_id=request_id,
        errors=[
            ErrorDetail(
                code=f"HTTP_{exc.status_code}",
                message=str(exc.detail),
            )
        ],
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode="json"),
        headers={"X-Request-ID": request_id},
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle request validation errors with detailed feedback.

    Args:
        request: The incoming request.
        exc: The validation error.

    Returns:
        JSON response with validation error details.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error.get("loc", []))
        errors.append(
            ErrorDetail(
                code="VALIDATION_ERROR",
                message=error.get("msg", "Validation error"),
                field=field if field else None,
                details={"type": error.get("type")},
            )
        )

    error_response = ErrorResponse(
        success=False,
        message="Request validation failed",
        request_id=request_id,
        errors=errors,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(mode="json"),
        headers={"X-Request-ID": request_id},
    )


async def global_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle any unhandled exceptions.

    Args:
        request: The incoming request.
        exc: The exception.

    Returns:
        JSON response with error details.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    settings = get_settings()

    logger.error(
        f"Unhandled exception: {exc}",
        extra={"request_id": request_id},
        exc_info=True,
    )

    error_details = str(exc) if settings.debug else "An unexpected error occurred"

    error_response = ErrorResponse(
        success=False,
        message="Internal server error",
        request_id=request_id,
        errors=[
            ErrorDetail(
                code="INTERNAL_ERROR",
                message=error_details,
                details={"traceback": traceback.format_exc()} if settings.debug else None,
            )
        ],
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode="json"),
        headers={"X-Request-ID": request_id},
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Configure exception handlers for the FastAPI application.

    Args:
        app: The FastAPI application instance.
    """
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)
