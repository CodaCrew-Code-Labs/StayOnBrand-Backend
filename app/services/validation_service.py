"""
Combined validation service for managing validation history and reruns.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.enums import ValidationStatus, ValidationType
from app.models.requests import ValidationHistoryParams, ValidationRerunRequest
from app.models.responses import (
    ValidationDetailResponse,
    ValidationHistoryItem,
    ValidationHistoryResponse,
    ValidationRerunResponse,
)
from app.services.redis_service import RedisService

logger = logging.getLogger(__name__)


class ValidationService:
    """
    Service for managing validation history and reruns.

    Provides methods for:
    - Retrieving validation history
    - Getting validation details
    - Rerunning previous validations
    """

    def __init__(self, redis_service: Optional[RedisService] = None):
        """
        Initialize validation service.

        Args:
            redis_service: Redis service for storage.
        """
        self._redis = redis_service

    async def get_history(
        self,
        user_id: str,
        params: ValidationHistoryParams,
    ) -> ValidationHistoryResponse:
        """
        Get validation history for a user.

        Args:
            user_id: The user ID to get history for.
            params: Pagination and filter parameters.

        Returns:
            ValidationHistoryResponse with history items.
        """
        # TODO: Implement history retrieval
        # - Query Redis/storage for user's validations
        # - Apply filters (type, status, date range)
        # - Apply sorting
        # - Apply pagination

        items = await self._fetch_history_items(user_id, params)
        total = await self._count_history_items(user_id, params)

        total_pages = (total + params.page_size - 1) // params.page_size

        return ValidationHistoryResponse(
            success=True,
            message="Validation history retrieved",
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
        )

    async def get_validation_detail(
        self,
        validation_id: str,
        user_id: str,
    ) -> ValidationDetailResponse:
        """
        Get detailed information about a specific validation.

        Args:
            validation_id: The validation ID.
            user_id: The requesting user's ID.

        Returns:
            ValidationDetailResponse with full details.

        Raises:
            ValueError: If validation not found or access denied.
        """
        # TODO: Implement validation detail retrieval
        # - Fetch validation from storage
        # - Verify user has access
        # - Return full validation details

        validation = await self._fetch_validation(validation_id)

        if not validation:
            raise ValueError(f"Validation {validation_id} not found")

        # Verify ownership
        if validation.get("user_id") != user_id:
            raise ValueError("Access denied to this validation")

        return ValidationDetailResponse(
            success=True,
            message="Validation details retrieved",
            validation_id=validation_id,
            validation_type=ValidationType(validation.get("type", "combined")),
            status=ValidationStatus(validation.get("status", "completed")),
            created_at=datetime.fromisoformat(validation.get("created_at", datetime.utcnow().isoformat())),
            completed_at=datetime.fromisoformat(validation["completed_at"]) if validation.get("completed_at") else None,
            request_params=validation.get("request_params", {}),
            result=validation.get("result"),
            error=validation.get("error"),
            image_metadata=None,  # TODO: Include if available
        )

    async def rerun_validation(
        self,
        validation_id: str,
        request: ValidationRerunRequest,
        user_id: str,
    ) -> ValidationRerunResponse:
        """
        Rerun a previous validation.

        Args:
            validation_id: The original validation ID.
            request: Rerun parameters.
            user_id: The requesting user's ID.

        Returns:
            ValidationRerunResponse with new validation ID.

        Raises:
            ValueError: If validation not found or access denied.
        """
        # TODO: Implement validation rerun
        # - Fetch original validation
        # - Verify user has access
        # - Create new validation with same or updated parameters
        # - Queue for processing

        original = await self._fetch_validation(validation_id)

        if not original:
            raise ValueError(f"Validation {validation_id} not found")

        if original.get("user_id") != user_id:
            raise ValueError("Access denied to this validation")

        # Create new validation
        new_validation_id = str(uuid.uuid4())

        # Merge parameters
        new_params = original.get("request_params", {}).copy()
        if request.override_params:
            new_params.update(request.override_params)

        # Store new validation
        await self._store_validation(
            new_validation_id,
            user_id,
            original.get("type", "combined"),
            new_params,
        )

        # TODO: Queue for actual processing
        # - Dispatch to appropriate service
        # - Handle cached vs new image

        return ValidationRerunResponse(
            success=True,
            message="Validation rerun initiated",
            new_validation_id=new_validation_id,
            original_validation_id=validation_id,
            status=ValidationStatus.PENDING,
        )

    async def store_validation_result(
        self,
        validation_id: str,
        user_id: str,
        validation_type: ValidationType,
        request_params: Dict[str, Any],
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Store a validation result.

        Args:
            validation_id: The validation ID.
            user_id: The user ID.
            validation_type: Type of validation.
            request_params: Original request parameters.
            result: Validation result if successful.
            error: Error message if failed.
        """
        # TODO: Implement result storage
        # - Store validation metadata
        # - Store result or error
        # - Update indexes for history queries

        status = ValidationStatus.COMPLETED if result else ValidationStatus.FAILED

        data = {
            "user_id": user_id,
            "type": validation_type.value,
            "status": status.value,
            "request_params": request_params,
            "result": result,
            "error": error,
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
        }

        if self._redis:
            await self._redis.set(f"validation:{validation_id}", data)

            # Add to user's history index
            await self._add_to_history_index(user_id, validation_id)

    async def _fetch_history_items(
        self,
        user_id: str,
        params: ValidationHistoryParams,
    ) -> List[ValidationHistoryItem]:
        """
        Fetch history items for a user.

        Args:
            user_id: The user ID.
            params: Query parameters.

        Returns:
            List of ValidationHistoryItem objects.
        """
        # TODO: Implement actual fetching from storage
        # - Get validation IDs from user's history index
        # - Apply filters
        # - Apply sorting
        # - Apply pagination
        # - Fetch validation summaries

        items = []

        if self._redis:
            # Get user's validation IDs
            history_key = f"user:{user_id}:validations"
            validation_ids = await self._redis.get(history_key) or []

            # Apply pagination
            start = (params.page - 1) * params.page_size
            end = start + params.page_size
            page_ids = validation_ids[start:end]

            # Fetch each validation
            for vid in page_ids:
                validation = await self._fetch_validation(vid)
                if validation:
                    # Apply filters
                    if params.validation_type and validation.get("type") != params.validation_type:
                        continue
                    if params.status and validation.get("status") != params.status:
                        continue

                    items.append(
                        ValidationHistoryItem(
                            validation_id=vid,
                            validation_type=ValidationType(validation.get("type", "combined")),
                            status=ValidationStatus(validation.get("status", "completed")),
                            created_at=datetime.fromisoformat(
                                validation.get("created_at", datetime.utcnow().isoformat())
                            ),
                            completed_at=datetime.fromisoformat(validation["completed_at"])
                            if validation.get("completed_at")
                            else None,
                            summary=self._generate_summary(validation),
                            compliance_score=validation.get("result", {}).get("compliance_score"),
                        )
                    )

        return items

    async def _count_history_items(
        self,
        user_id: str,
        params: ValidationHistoryParams,
    ) -> int:
        """
        Count total history items for pagination.

        Args:
            user_id: The user ID.
            params: Query parameters.

        Returns:
            Total count of matching items.
        """
        # TODO: Implement actual counting with filters
        if self._redis:
            history_key = f"user:{user_id}:validations"
            validation_ids = await self._redis.get(history_key) or []
            return len(validation_ids)
        return 0

    async def _fetch_validation(self, validation_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single validation by ID.

        Args:
            validation_id: The validation ID.

        Returns:
            Validation data dict or None.
        """
        # TODO: Implement actual fetching
        if self._redis:
            return await self._redis.get(f"validation:{validation_id}")
        return None

    async def _store_validation(
        self,
        validation_id: str,
        user_id: str,
        validation_type: str,
        request_params: Dict[str, Any],
    ) -> None:
        """
        Store a new validation record.

        Args:
            validation_id: The validation ID.
            user_id: The user ID.
            validation_type: Type of validation.
            request_params: Request parameters.
        """
        # TODO: Implement validation storage
        data = {
            "user_id": user_id,
            "type": validation_type,
            "status": ValidationStatus.PENDING.value,
            "request_params": request_params,
            "created_at": datetime.utcnow().isoformat(),
        }

        if self._redis:
            await self._redis.set(f"validation:{validation_id}", data)
            await self._add_to_history_index(user_id, validation_id)

    async def _add_to_history_index(
        self,
        user_id: str,
        validation_id: str,
    ) -> None:
        """
        Add validation to user's history index.

        Args:
            user_id: The user ID.
            validation_id: The validation ID.
        """
        # TODO: Implement index management
        if self._redis:
            history_key = f"user:{user_id}:validations"
            history = await self._redis.get(history_key) or []
            history.insert(0, validation_id)  # Most recent first
            await self._redis.set(history_key, history)

    def _generate_summary(self, validation: Dict[str, Any]) -> str:
        """
        Generate a summary string for a validation.

        Args:
            validation: Validation data.

        Returns:
            Summary string.
        """
        # TODO: Implement summary generation based on validation type
        validation_type = validation.get("type", "unknown")
        status = validation.get("status", "unknown")

        if status == "completed":
            score = validation.get("result", {}).get("compliance_score")
            if score is not None:
                return f"{validation_type} validation completed with {score:.1f}% compliance"
            return f"{validation_type} validation completed"
        elif status == "failed":
            return f"{validation_type} validation failed: {validation.get('error', 'Unknown error')}"
        else:
            return f"{validation_type} validation {status}"


# Factory function
def get_validation_service(redis_service: Optional[RedisService] = None) -> ValidationService:
    """Get validation service instance."""
    return ValidationService(redis_service)
