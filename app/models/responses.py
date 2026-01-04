"""
Response models for API endpoints.
"""

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from app.models.common import BaseResponse, BoundingBox, Color, ImageMetadata
from app.models.enums import (
    BrandComplianceLevel,
    ContrastRating,
    ValidationStatus,
    ValidationType,
    WCAGLevel,
)


# Color Contrast Responses
class ColorRecommendation(BaseModel):
    """Recommended color adjustment."""

    original_color: str = Field(..., description="Original color")
    suggested_color: str = Field(..., description="Suggested alternative color")
    contrast_ratio: float = Field(..., description="Resulting contrast ratio")
    passes_wcag: bool = Field(..., description="Whether suggestion passes WCAG")
    adjustment_type: str = Field(..., description="Type of adjustment made")


class ColorCompareResponse(BaseResponse):
    """Response for color contrast comparison."""

    foreground_color: str = Field(..., description="Foreground color analyzed")
    background_color: str = Field(..., description="Background color analyzed")
    contrast_ratio: float = Field(..., description="Calculated contrast ratio")
    rating: ContrastRating = Field(..., description="Contrast rating")
    passes_aa_normal: bool = Field(..., description="Passes WCAG AA for normal text")
    passes_aa_large: bool = Field(..., description="Passes WCAG AA for large text")
    passes_aaa_normal: bool = Field(..., description="Passes WCAG AAA for normal text")
    passes_aaa_large: bool = Field(..., description="Passes WCAG AAA for large text")
    recommendations: Optional[List[ColorRecommendation]] = Field(
        None,
        description="Color recommendations if contrast is insufficient",
    )


# Brand Validation Responses
class BrandColorMatch(BaseModel):
    """Brand color matching result."""

    detected_color: str = Field(..., description="Color detected in image")
    matched_brand_color: Optional[str] = Field(None, description="Matched brand color")
    match_percentage: float = Field(..., description="Match percentage")
    coverage_percentage: float = Field(..., description="Coverage in image")
    is_compliant: bool = Field(..., description="Whether color is brand compliant")


class BrandValidationResult(BaseModel):
    """Individual brand validation result."""

    rule_name: str = Field(..., description="Name of the validation rule")
    passed: bool = Field(..., description="Whether the rule passed")
    message: str = Field(..., description="Validation message")
    severity: str = Field(..., description="Severity level (error, warning, info)")
    details: Optional[dict[str, Any]] = Field(None, description="Additional details")


class BrandValidationResponse(BaseResponse):
    """Response for brand image validation."""

    validation_id: str = Field(..., description="Unique validation ID")
    compliance_level: BrandComplianceLevel = Field(..., description="Overall compliance level")
    compliance_score: float = Field(..., description="Compliance score (0-100)")
    color_matches: List[BrandColorMatch] = Field(..., description="Color matching results")
    validation_results: List[BrandValidationResult] = Field(
        ...,
        description="Individual validation results",
    )
    image_metadata: ImageMetadata = Field(..., description="Image metadata")
    processed_at: datetime = Field(..., description="Processing timestamp")


class ExtractedColor(BaseModel):
    """Extracted color with metadata."""

    color: Color = Field(..., description="Color details")
    percentage: float = Field(..., description="Percentage of image")
    pixel_count: int = Field(..., description="Number of pixels")
    is_dominant: bool = Field(..., description="Whether this is a dominant color")


class ExtractedColorsResponse(BaseResponse):
    """Response for color extraction."""

    validation_id: str = Field(..., description="Unique validation ID")
    colors: List[ExtractedColor] = Field(..., description="Extracted colors")
    total_colors_found: int = Field(..., description="Total unique colors found")
    dominant_color: Color = Field(..., description="Most dominant color")
    palette_type: str = Field(..., description="Detected palette type")
    image_metadata: ImageMetadata = Field(..., description="Image metadata")


class ImageDifference(BaseModel):
    """Difference between two images."""

    difference_type: str = Field(..., description="Type of difference")
    location: Optional[BoundingBox] = Field(None, description="Location of difference")
    severity: str = Field(..., description="Severity of difference")
    description: str = Field(..., description="Description of difference")


class ImageComparisonResponse(BaseResponse):
    """Response for image comparison."""

    validation_id: str = Field(..., description="Unique validation ID")
    similarity_score: float = Field(..., description="Overall similarity score (0-100)")
    are_identical: bool = Field(..., description="Whether images are identical")
    color_similarity: float = Field(..., description="Color similarity score")
    layout_similarity: Optional[float] = Field(None, description="Layout similarity score")
    differences: List[ImageDifference] = Field(..., description="List of differences found")
    image1_metadata: ImageMetadata = Field(..., description="First image metadata")
    image2_metadata: ImageMetadata = Field(..., description="Second image metadata")


# WCAG Validation Responses
class WCAGIssue(BaseModel):
    """WCAG compliance issue."""

    criterion: str = Field(..., description="WCAG criterion (e.g., 1.4.3)")
    level: WCAGLevel = Field(..., description="WCAG level")
    title: str = Field(..., description="Issue title")
    description: str = Field(..., description="Issue description")
    impact: str = Field(..., description="Impact level")
    location: Optional[BoundingBox] = Field(None, description="Location in image")
    suggestion: Optional[str] = Field(None, description="Suggested fix")


class WCAGValidationResponse(BaseResponse):
    """Response for WCAG image validation."""

    validation_id: str = Field(..., description="Unique validation ID")
    is_compliant: bool = Field(..., description="Whether image is WCAG compliant")
    compliance_score: float = Field(..., description="Compliance score (0-100)")
    wcag_level_achieved: WCAGLevel = Field(..., description="Highest level achieved")
    issues: List[WCAGIssue] = Field(..., description="List of WCAG issues found")
    passed_criteria: List[str] = Field(..., description="List of passed criteria")
    suggestions: List[str] = Field(..., description="Improvement suggestions")
    image_metadata: ImageMetadata = Field(..., description="Image metadata")
    processed_at: datetime = Field(..., description="Processing timestamp")


class WCAGTextContrastResponse(BaseResponse):
    """Response for WCAG text contrast validation."""

    validation_id: str = Field(..., description="Unique validation ID")
    contrast_ratio: float = Field(..., description="Calculated contrast ratio")
    is_compliant: bool = Field(..., description="Whether contrast is compliant")
    required_ratio: float = Field(..., description="Required ratio for target level")
    wcag_level: WCAGLevel = Field(..., description="Evaluated WCAG level")
    text_size_category: str = Field(..., description="Text size category")
    passes_aa: bool = Field(..., description="Passes WCAG AA")
    passes_aaa: bool = Field(..., description="Passes WCAG AAA")
    recommendations: Optional[List[ColorRecommendation]] = Field(
        None,
        description="Color recommendations if non-compliant",
    )


class WCAGCriterion(BaseModel):
    """WCAG criterion definition."""

    id: str = Field(..., description="Criterion ID (e.g., 1.4.3)")
    title: str = Field(..., description="Criterion title")
    level: WCAGLevel = Field(..., description="Conformance level")
    description: str = Field(..., description="Criterion description")
    how_to_meet: str = Field(..., description="How to meet the criterion")
    techniques: List[str] = Field(..., description="Sufficient techniques")


class WCAGRequirementsResponse(BaseResponse):
    """Response for WCAG requirements listing."""

    version: str = Field(..., description="WCAG version")
    criteria: List[WCAGCriterion] = Field(..., description="List of criteria")
    total_level_a: int = Field(..., description="Total Level A criteria")
    total_level_aa: int = Field(..., description="Total Level AA criteria")
    total_level_aaa: int = Field(..., description="Total Level AAA criteria")


# Validation History Responses
class ValidationHistoryItem(BaseModel):
    """Single validation history entry."""

    validation_id: str = Field(..., description="Validation ID")
    validation_type: ValidationType = Field(..., description="Type of validation")
    status: ValidationStatus = Field(..., description="Validation status")
    created_at: datetime = Field(..., description="Creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    summary: str = Field(..., description="Brief summary of results")
    compliance_score: Optional[float] = Field(None, description="Compliance score if applicable")


class ValidationHistoryResponse(BaseResponse):
    """Response for validation history listing."""

    items: List[ValidationHistoryItem] = Field(..., description="History items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total pages")


class ValidationDetailResponse(BaseResponse):
    """Detailed validation response."""

    validation_id: str = Field(..., description="Validation ID")
    validation_type: ValidationType = Field(..., description="Type of validation")
    status: ValidationStatus = Field(..., description="Validation status")
    created_at: datetime = Field(..., description="Creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    request_params: dict[str, Any] = Field(..., description="Original request parameters")
    result: Optional[dict[str, Any]] = Field(None, description="Validation result")
    error: Optional[str] = Field(None, description="Error message if failed")
    image_metadata: Optional[ImageMetadata] = Field(None, description="Image metadata")


class ValidationRerunResponse(BaseResponse):
    """Response for validation rerun."""

    new_validation_id: str = Field(..., description="New validation ID")
    original_validation_id: str = Field(..., description="Original validation ID")
    status: ValidationStatus = Field(..., description="New validation status")
    message: str = Field(..., description="Status message")


# Utility Responses
class SupportedFormat(BaseModel):
    """Supported file format."""

    extension: str = Field(..., description="File extension")
    mime_type: str = Field(..., description="MIME type")
    max_size_mb: int = Field(..., description="Maximum file size in MB")
    description: str = Field(..., description="Format description")


class SupportedFormatsResponse(BaseResponse):
    """Response for supported formats listing."""

    image_formats: List[SupportedFormat] = Field(..., description="Supported image formats")
    max_file_size_mb: int = Field(..., description="Maximum file size")
    max_dimensions: dict[str, int] = Field(..., description="Maximum image dimensions")
