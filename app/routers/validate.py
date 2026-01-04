"""
Combined validation and history endpoints.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_current_user, get_validation_service_dep
from app.models.common import User
from app.models.requests import ValidationHistoryParams, ValidationRerunRequest
from app.models.responses import (
    ValidationDetailResponse,
    ValidationHistoryResponse,
    ValidationRerunResponse,
)
from app.services.validation_service import ValidationService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/validate",
    tags=["Validation History"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing authentication"},
        404: {"description": "Validation not found"},
        422: {"description": "Validation Error"},
        500: {"description": "Internal Server Error"},
    },
)


@router.get(
    "/history",
    response_model=ValidationHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get validation history",
    description="""
    Retrieve the validation history for the authenticated user.

    This endpoint returns a paginated list of past validations with
    filtering and sorting options. Each item includes basic information
    about the validation including type, status, and compliance score.
    """,
    responses={
        200: {
            "description": "Validation history retrieved successfully",
        },
    },
)
async def get_history(
    current_user: Annotated[User, Depends(get_current_user)],
    validation_service: Annotated[ValidationService, Depends(get_validation_service_dep)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    validation_type: Annotated[str | None, Query(description="Filter by type")] = None,
    validation_status: Annotated[
        str | None, Query(alias="status", description="Filter by status")
    ] = None,
    start_date: Annotated[
        str | None, Query(description="Filter by start date (ISO format)")
    ] = None,
    end_date: Annotated[str | None, Query(description="Filter by end date (ISO format)")] = None,
    sort_by: Annotated[str, Query(description="Field to sort by")] = "created_at",
    sort_order: Annotated[str, Query(description="Sort order (asc/desc)")] = "desc",
) -> ValidationHistoryResponse:
    """
    Get validation history for the current user.

    Args:
        current_user: The authenticated user.
        validation_service: The validation service.
        page: Page number (starting from 1).
        page_size: Number of items per page (1-100).
        validation_type: Optional filter by validation type.
        validation_status: Optional filter by validation status.
        start_date: Optional filter for validations after this date.
        end_date: Optional filter for validations before this date.
        sort_by: Field to sort by (default: created_at).
        sort_order: Sort order - 'asc' or 'desc' (default: desc).

    Returns:
        ValidationHistoryResponse with paginated history items.
    """
    # TODO: Implement history retrieval
    # - Build query parameters
    # - Fetch history from service
    # - Return paginated response

    params = ValidationHistoryParams(
        page=page,
        page_size=page_size,
        validation_type=validation_type,
        status=validation_status,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    logger.info(f"Validation history requested by user {current_user.id}")

    response = await validation_service.get_history(
        user_id=current_user.id,
        params=params,
    )

    return response


@router.get(
    "/{validation_id}",
    response_model=ValidationDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get validation details",
    description="""
    Retrieve detailed information about a specific validation.

    This endpoint returns the complete details of a validation including
    the original request parameters, full results, and any errors that
    occurred during processing.
    """,
    responses={
        200: {
            "description": "Validation details retrieved successfully",
        },
        404: {
            "description": "Validation not found",
        },
    },
)
async def get_validation_detail(
    validation_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    validation_service: Annotated[ValidationService, Depends(get_validation_service_dep)],
) -> ValidationDetailResponse:
    """
    Get detailed information about a specific validation.

    Args:
        validation_id: The unique validation ID.
        current_user: The authenticated user.
        validation_service: The validation service.

    Returns:
        ValidationDetailResponse with full validation details.

    Raises:
        HTTPException: If validation not found or access denied.
    """
    # TODO: Implement detail retrieval
    # - Fetch validation from service
    # - Verify user has access
    # - Return full details

    logger.info(
        f"Validation detail requested by user {current_user.id}: " f"validation_id={validation_id}"
    )

    try:
        response = await validation_service.get_validation_detail(
            validation_id=validation_id,
            user_id=current_user.id,
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "VALIDATION_NOT_FOUND",
                "message": str(e),
            },
        )


@router.post(
    "/{validation_id}/rerun",
    response_model=ValidationRerunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Rerun a validation",
    description="""
    Rerun a previous validation with optional parameter overrides.

    This endpoint creates a new validation based on a previous one,
    allowing you to rerun the same analysis or modify specific parameters.
    The original validation remains unchanged.
    """,
    responses={
        202: {
            "description": "Validation rerun initiated",
        },
        404: {
            "description": "Original validation not found",
        },
    },
)
async def rerun_validation(
    validation_id: str,
    request: ValidationRerunRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    validation_service: Annotated[ValidationService, Depends(get_validation_service_dep)],
) -> ValidationRerunResponse:
    """
    Rerun a previous validation.

    Args:
        validation_id: The ID of the original validation to rerun.
        request: Rerun parameters including optional overrides.
        current_user: The authenticated user.
        validation_service: The validation service.

    Returns:
        ValidationRerunResponse with new validation ID and status.

    Raises:
        HTTPException: If original validation not found or access denied.
    """
    # TODO: Implement validation rerun
    # - Fetch original validation
    # - Verify user has access
    # - Create new validation with merged parameters
    # - Queue for processing
    # - Return new validation info

    logger.info(
        f"Validation rerun requested by user {current_user.id}: " f"original_id={validation_id}"
    )

    try:
        response = await validation_service.rerun_validation(
            validation_id=validation_id,
            request=request,
            user_id=current_user.id,
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "VALIDATION_NOT_FOUND",
                "message": str(e),
            },
        )
