"""
Pydantic models for request/response validation.
"""

from app.models.common import (
    BaseResponse,
    ErrorDetail,
    ErrorResponse,
    PaginatedResponse,
    HealthResponse,
    User,
)
from app.models.enums import (
    ValidationStatus,
    ValidationType,
    WCAGLevel,
    WCAGVersion,
    ColorFormat,
    ImageFormat,
    ContrastRating,
)
from app.models.requests import (
    ColorCompareRequest,
    BrandValidateImageRequest,
    BrandExtractColorsRequest,
    BrandCompareImagesRequest,
    WCAGValidateImageRequest,
    WCAGValidateTextContrastRequest,
    ValidationRerunRequest,
)
from app.models.responses import (
    ColorCompareResponse,
    ColorRecommendation,
    BrandValidationResponse,
    ExtractedColorsResponse,
    ImageComparisonResponse,
    WCAGValidationResponse,
    WCAGTextContrastResponse,
    WCAGRequirementsResponse,
    ValidationHistoryResponse,
    ValidationDetailResponse,
    ValidationRerunResponse,
    SupportedFormatsResponse,
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
