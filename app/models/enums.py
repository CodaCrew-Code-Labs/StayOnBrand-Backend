"""
Enumeration types for the StayOnBoard API.
"""

from enum import Enum


class ValidationStatus(str, Enum):
    """Status of a validation request."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ValidationType(str, Enum):
    """Type of validation performed."""

    COLOR_CONTRAST = "color_contrast"
    BRAND_IMAGE = "brand_image"
    BRAND_COLORS = "brand_colors"
    BRAND_COMPARE = "brand_compare"
    WCAG_IMAGE = "wcag_image"
    WCAG_TEXT_CONTRAST = "wcag_text_contrast"
    COMBINED = "combined"


class WCAGLevel(str, Enum):
    """WCAG conformance levels."""

    A = "A"
    AA = "AA"
    AAA = "AAA"


class WCAGVersion(str, Enum):
    """WCAG versions supported."""

    WCAG_20 = "2.0"
    WCAG_21 = "2.1"
    WCAG_22 = "2.2"


class ColorFormat(str, Enum):
    """Supported color format representations."""

    HEX = "hex"
    RGB = "rgb"
    RGBA = "rgba"
    HSL = "hsl"
    HSLA = "hsla"


class ImageFormat(str, Enum):
    """Supported image formats."""

    JPEG = "jpeg"
    JPG = "jpg"
    PNG = "png"
    GIF = "gif"
    WEBP = "webp"
    SVG = "svg"


class ContrastRating(str, Enum):
    """Contrast ratio rating categories."""

    FAIL = "fail"
    AA_LARGE = "aa_large"
    AA = "aa"
    AAA = "aaa"


class TextSize(str, Enum):
    """Text size categories for WCAG contrast requirements."""

    NORMAL = "normal"
    LARGE = "large"


class ComponentType(str, Enum):
    """UI component types for validation."""

    TEXT = "text"
    BUTTON = "button"
    LINK = "link"
    ICON = "icon"
    GRAPHIC = "graphic"


class BrandComplianceLevel(str, Enum):
    """Brand compliance assessment levels."""

    COMPLIANT = "compliant"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"
