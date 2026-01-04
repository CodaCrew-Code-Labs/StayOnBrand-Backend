"""
Pydantic models for request/response validation.
"""

from app.models.common import (
    BaseResponse,
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    PaginatedResponse,
    User,
)
from app.models.enums import (
    ColorFormat,
    ContrastRating,
    ImageFormat,
    ValidationStatus,
    ValidationType,
    WCAGLevel,
    WCAGVersion,
)
from app.models.requests import (
    BrandCompareImagesRequest,
    BrandExtractColorsRequest,
    BrandValidateImageRequest,
    ColorCompareRequest,
    ValidationRerunRequest,
    WCAGValidateImageRequest,
    WCAGValidateTextContrastRequest,
)
from app.models.responses import (
    BrandValidationResponse,
    ColorCompareResponse,
    ColorRecommendation,
    ExtractedColorsResponse,
    ImageComparisonResponse,
    SupportedFormatsResponse,
    ValidationDetailResponse,
    ValidationHistoryResponse,
    ValidationRerunResponse,
    WCAGRequirementsResponse,
    WCAGTextContrastResponse,
    WCAGValidationResponse,
)

__all__ = [
    # Common
    "BaseResponse",
    "ErrorDetail",
    "ErrorResponse",
    "PaginatedResponse",
    "HealthResponse",
    "User",
    # Enums
    "ValidationStatus",
    "ValidationType",
    "WCAGLevel",
    "WCAGVersion",
    "ColorFormat",
    "ImageFormat",
    "ContrastRating",
    # Requests
    "ColorCompareRequest",
    "BrandValidateImageRequest",
    "BrandExtractColorsRequest",
    "BrandCompareImagesRequest",
    "WCAGValidateImageRequest",
    "WCAGValidateTextContrastRequest",
    "ValidationRerunRequest",
    # Responses
    "ColorCompareResponse",
    "ColorRecommendation",
    "BrandValidationResponse",
    "ExtractedColorsResponse",
    "ImageComparisonResponse",
    "WCAGValidationResponse",
    "WCAGTextContrastResponse",
    "WCAGRequirementsResponse",
    "ValidationHistoryResponse",
    "ValidationDetailResponse",
    "ValidationRerunResponse",
    "SupportedFormatsResponse",
]
