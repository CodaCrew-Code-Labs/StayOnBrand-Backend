"""
Request models for API endpoints.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.models.enums import ColorFormat, WCAGLevel, WCAGVersion


class ColorCompareRequest(BaseModel):
    """Request model for color contrast comparison."""

    colors: list[str] = Field(
        ...,
        description="List of colors in hex format (min 2, max 5)",
        min_length=2,
        max_length=5,
        examples=[["#FFFFFF", "#000000"]],
    )

    @field_validator("colors")
    @classmethod
    def validate_colors(cls, v: list[str]) -> list[str]:
        """Validate color format."""
        import re

        hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")
        for color in v:
            if not hex_pattern.match(color):
                raise ValueError(f"Invalid hex color format: {color}")
        return v


class BrandValidateImageRequest(BaseModel):
    """Request model for brand image validation."""

    brand_id: str | None = Field(
        None,
        description="Brand ID to validate against (uses default if not provided)",
    )
    brand_colors: list[str] | None = Field(
        None,
        description="List of brand colors in hex format",
    )
    tolerance_percentage: float = Field(
        default=10.0,
        ge=0,
        le=100,
        description="Color matching tolerance percentage",
    )
    check_logo_presence: bool = Field(
        default=False,
        description="Whether to check for logo presence",
    )
    logo_reference_url: str | None = Field(
        None,
        description="URL to reference logo for comparison",
    )
    additional_rules: dict[str, Any] | None = Field(
        None,
        description="Additional brand validation rules",
    )

    @field_validator("brand_colors")
    @classmethod
    def validate_brand_colors(cls, v: list[str] | None) -> list[str] | None:
        """Validate brand colors format."""
        if v is not None:
            import re

            hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")
            for color in v:
                if not hex_pattern.match(color):
                    raise ValueError(f"Invalid hex color format: {color}")
        return v


class BrandExtractColorsRequest(BaseModel):
    """Request model for color extraction from image."""

    max_colors: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of colors to extract",
    )
    include_percentages: bool = Field(
        default=True,
        description="Include color usage percentages",
    )
    color_format: ColorFormat = Field(
        default=ColorFormat.HEX,
        description="Output color format",
    )
    group_similar: bool = Field(
        default=True,
        description="Group similar colors together",
    )
    similarity_threshold: float = Field(
        default=15.0,
        ge=0,
        le=100,
        description="Threshold for grouping similar colors",
    )


class BrandCompareImagesRequest(BaseModel):
    """Request model for comparing two images."""

    comparison_type: str = Field(
        default="visual",
        description="Type of comparison (visual, colors, layout)",
    )
    include_color_diff: bool = Field(
        default=True,
        description="Include color difference analysis",
    )
    include_layout_diff: bool = Field(
        default=False,
        description="Include layout difference analysis",
    )
    sensitivity: float = Field(
        default=0.9,
        ge=0,
        le=1,
        description="Comparison sensitivity (0-1)",
    )


class WCAGValidateImageRequest(BaseModel):
    """Request model for WCAG image validation."""

    wcag_version: WCAGVersion = Field(
        default=WCAGVersion.WCAG_21,
        description="WCAG version to validate against",
    )
    wcag_level: WCAGLevel = Field(
        default=WCAGLevel.AA,
        description="Target WCAG conformance level",
    )
    check_alt_text: bool = Field(
        default=True,
        description="Check for proper alt text usage",
    )
    check_color_contrast: bool = Field(
        default=True,
        description="Check color contrast compliance",
    )
    check_text_size: bool = Field(
        default=True,
        description="Check minimum text size requirements",
    )
    check_touch_targets: bool = Field(
        default=False,
        description="Check touch target sizes",
    )
    include_suggestions: bool = Field(
        default=True,
        description="Include accessibility improvement suggestions",
    )


class WCAGValidateTextContrastRequest(BaseModel):
    """Request model for WCAG text contrast validation."""

    foreground_color: str = Field(
        ...,
        description="Text color in hex format",
        pattern=r"^#[0-9A-Fa-f]{6}$",
    )
    background_color: str = Field(
        ...,
        description="Background color in hex format",
        pattern=r"^#[0-9A-Fa-f]{6}$",
    )
    text_size_px: float | None = Field(
        None,
        description="Text size in pixels",
    )
    is_bold: bool = Field(
        default=False,
        description="Whether the text is bold",
    )
    wcag_version: WCAGVersion = Field(
        default=WCAGVersion.WCAG_21,
        description="WCAG version to validate against",
    )
    wcag_level: WCAGLevel = Field(
        default=WCAGLevel.AA,
        description="Target WCAG conformance level",
    )


class ValidationRerunRequest(BaseModel):
    """Request model for rerunning a validation."""

    use_cached_image: bool = Field(
        default=True,
        description="Whether to use cached image or require new upload",
    )
    override_params: dict[str, Any] | None = Field(
        None,
        description="Parameters to override from original validation",
    )


class ValidationHistoryParams(BaseModel):
    """Query parameters for validation history."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    validation_type: str | None = Field(None, description="Filter by validation type")
    status: str | None = Field(None, description="Filter by status")
    start_date: str | None = Field(None, description="Filter by start date (ISO format)")
    end_date: str | None = Field(None, description="Filter by end date (ISO format)")
    sort_by: str = Field(default="created_at", description="Field to sort by")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")