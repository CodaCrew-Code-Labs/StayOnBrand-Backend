"""
Response models for API endpoints.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.common import BaseResponse, BoundingBox, Color, ImageMetadata
from app.models.enums import (
    BrandComplianceLevel,
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

    colors: list[str] = Field(..., description="Colors analyzed")
    comparisons: dict[str, dict[str, Any]] = Field(
        ..., description="Color pair comparisons with WCAG validation results"
    )
    color_scores: dict[str, float] = Field(
        ..., description="Individual color accessibility scores (0-100)"
    )
    palette_score: float = Field(..., description="Overall palette accessibility score (0-100)")


# Brand Validation Responses
class DetectedColorMatch(BaseModel):
    """A detected color in the image matched to its nearest brand color."""

    detected_color: str = Field(..., description="Hex color detected in the image")
    detected_color_name: str = Field(..., description="Human-readable color name")
    nearest_brand_color: str = Field(..., description="Nearest brand color hex")
    match_percentage: float = Field(..., description="How close the match is (0-100)")
    coverage_percentage: float = Field(..., description="How much of the image this color covers")
    description: str = Field(
        ...,
        description="Human-readable description, e.g. 'This teal is close to brand blue: 92% match'",
    )


class BrandColorMatch(BaseModel):
    """Brand color matching result."""

    detected_color: str = Field(..., description="Color detected in image")
    matched_brand_color: str | None = Field(None, description="Matched brand color")
    match_percentage: float = Field(..., description="Match percentage")
    coverage_percentage: float = Field(..., description="Coverage in image")
    is_compliant: bool = Field(..., description="Whether color is brand compliant")


class BrandValidationResult(BaseModel):
    """Individual brand validation result."""

    rule_name: str = Field(..., description="Name of the validation rule")
    passed: bool = Field(..., description="Whether the rule passed")
    message: str = Field(..., description="Validation message")
    severity: str = Field(..., description="Severity level (error, warning, info)")
    details: dict[str, Any] | None = Field(None, description="Additional details")


class BrandValidationResponse(BaseResponse):
    """Response for brand image validation."""

    validation_id: str = Field(..., description="Unique validation ID")
    brand_color_match: str = Field(
        ..., description="Single score summary, e.g. 'Brand color match: 74%'"
    )
    compliance_score: float = Field(..., description="Compliance score (0-100)")
    compliance_level: BrandComplianceLevel = Field(..., description="Overall compliance level")
    top_color_matches: list[DetectedColorMatch] = Field(
        ...,
        description="Top 3 detected colors with their nearest brand color matches",
    )
    heatmap_image: str | None = Field(
        None,
        description="Base64-encoded PNG heatmap overlay (green=on-brand, red=off-brand). Only included if requested.",
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
    colors: list[ExtractedColor] = Field(..., description="Extracted colors")
    total_colors_found: int = Field(..., description="Total unique colors found")
    dominant_color: Color = Field(..., description="Most dominant color")
    palette_type: str = Field(..., description="Detected palette type")
    image_metadata: ImageMetadata = Field(..., description="Image metadata")


class ImageDifference(BaseModel):
    """Difference between two images."""

    difference_type: str = Field(..., description="Type of difference")
    location: BoundingBox | None = Field(None, description="Location of difference")
    severity: str = Field(..., description="Severity of difference")
    description: str = Field(..., description="Description of difference")


class ImageComparisonResponse(BaseResponse):
    """Response for image comparison."""

    validation_id: str = Field(..., description="Unique validation ID")
    similarity_score: float = Field(..., description="Overall similarity score (0-100)")
    are_identical: bool = Field(..., description="Whether images are identical")
    color_similarity: float = Field(..., description="Color similarity score")
    layout_similarity: float | None = Field(None, description="Layout similarity score")
    differences: list[ImageDifference] = Field(..., description="List of differences found")
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
    location: BoundingBox | None = Field(None, description="Location in image")
    suggestion: str | None = Field(None, description="Suggested fix")


class WCAGValidationResponse(BaseResponse):
    """Response for WCAG image validation."""

    validation_id: str = Field(..., description="Unique validation ID")
    is_compliant: bool = Field(..., description="Whether image is WCAG compliant")
    compliance_score: float = Field(..., description="Compliance score (0-100)")
    wcag_level_achieved: WCAGLevel = Field(..., description="Highest level achieved")
    issues: list[WCAGIssue] = Field(..., description="List of WCAG issues found")
    passed_criteria: list[str] = Field(..., description="List of passed criteria")
    suggestions: list[str] = Field(..., description="Improvement suggestions")
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
    recommendations: list[ColorRecommendation] | None = Field(
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
    techniques: list[str] = Field(..., description="Sufficient techniques")


class WCAGRequirementsResponse(BaseResponse):
    """Response for WCAG requirements listing."""

    version: str = Field(..., description="WCAG version")
    criteria: list[WCAGCriterion] = Field(..., description="List of criteria")
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
    completed_at: datetime | None = Field(None, description="Completion timestamp")
    summary: str = Field(..., description="Brief summary of results")
    compliance_score: float | None = Field(None, description="Compliance score if applicable")


class ValidationHistoryResponse(BaseResponse):
    """Response for validation history listing."""

    items: list[ValidationHistoryItem] = Field(..., description="History items")
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
    completed_at: datetime | None = Field(None, description="Completion timestamp")
    request_params: dict[str, Any] = Field(..., description="Original request parameters")
    result: dict[str, Any] | None = Field(None, description="Validation result")
    error: str | None = Field(None, description="Error message if failed")
    image_metadata: ImageMetadata | None = Field(None, description="Image metadata")


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

    image_formats: list[SupportedFormat] = Field(..., description="Supported image formats")
    max_file_size_mb: int = Field(..., description="Maximum file size")
    max_dimensions: dict[str, int] = Field(..., description="Maximum image dimensions")
