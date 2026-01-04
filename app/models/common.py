"""
Common Pydantic models used across the application.
"""

from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class BaseResponse(BaseModel):
    """Base response model with common fields."""

    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Human-readable message")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp",
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ErrorDetail(BaseModel):
    """Detailed error information."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    field: Optional[str] = Field(None, description="Field that caused the error")
    details: Optional[dict[str, Any]] = Field(None, description="Additional details")


class ErrorResponse(BaseResponse):
    """Error response model."""

    success: bool = Field(default=False)
    errors: List[ErrorDetail] = Field(default_factory=list, description="List of errors")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


class PaginatedResponse(BaseResponse, Generic[T]):
    """Paginated response wrapper."""

    data: List[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")


class HealthResponse(BaseResponse):
    """Health check response."""

    status: str = Field(..., description="Health status")
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Environment name")
    dependencies: dict[str, str] = Field(
        default_factory=dict,
        description="Status of dependencies",
    )


class User(BaseModel):
    """Authenticated user model."""

    id: str = Field(..., description="User ID")
    email: Optional[str] = Field(None, description="User email")
    organization_id: Optional[str] = Field(None, description="Organization ID")
    roles: List[str] = Field(default_factory=list, description="User roles")
    permissions: List[str] = Field(default_factory=list, description="User permissions")


class Color(BaseModel):
    """Color representation model."""

    hex: str = Field(..., description="Hex color code (e.g., #FF5733)", pattern=r"^#[0-9A-Fa-f]{6}$")
    rgb: Optional[dict[str, int]] = Field(None, description="RGB values")
    hsl: Optional[dict[str, float]] = Field(None, description="HSL values")
    name: Optional[str] = Field(None, description="Color name if identified")


class ColorPair(BaseModel):
    """A pair of colors for contrast analysis."""

    foreground: Color = Field(..., description="Foreground color")
    background: Color = Field(..., description="Background color")


class BoundingBox(BaseModel):
    """Bounding box coordinates for detected elements."""

    x: int = Field(..., description="X coordinate")
    y: int = Field(..., description="Y coordinate")
    width: int = Field(..., description="Width in pixels")
    height: int = Field(..., description="Height in pixels")


class ImageMetadata(BaseModel):
    """Metadata for uploaded images."""

    filename: str = Field(..., description="Original filename")
    size_bytes: int = Field(..., description="File size in bytes")
    width: Optional[int] = Field(None, description="Image width in pixels")
    height: Optional[int] = Field(None, description="Image height in pixels")
    format: str = Field(..., description="Image format")
    mime_type: str = Field(..., description="MIME type")


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
