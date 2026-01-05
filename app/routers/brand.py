"""
Brand validation endpoints.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.dependencies import get_brand_service_dep, get_current_user
from app.models.common import User
from app.models.requests import (
    BrandCompareImagesRequest,
    BrandExtractColorsRequest,
    BrandValidateImageRequest,
)
from app.models.responses import (
    BrandValidationResponse,
    ExtractedColorsResponse,
    ImageComparisonResponse,
)
from app.services.brand_service import BrandService
from app.utils.file_validation import validate_image_file

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/brand",
    tags=["Brand Validation"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing authentication"},
        400: {"description": "Bad Request - Invalid file or parameters"},
        422: {"description": "Validation Error"},
        500: {"description": "Internal Server Error"},
    },
)


@router.post(
    "/validate-image",
    response_model=BrandValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate image against brand guidelines",
    description="""
    Validate an uploaded image against brand guidelines and color specifications.

    This endpoint analyzes an image to check:
    - Color compliance with brand palette
    - Logo presence and placement (if configured)
    - Additional custom brand rules

    The response includes a compliance score, detailed color matches,
    and individual validation rule results.
    """,
    responses={
        200: {
            "description": "Successful brand validation",
        },
    },
)
async def validate_image(
    image: Annotated[UploadFile, File(description="Image file to validate")],
    current_user: Annotated[User, Depends(get_current_user)],
    brand_service: Annotated[BrandService, Depends(get_brand_service_dep)],
    brand_colors: Annotated[
        str, Form(description="Comma-separated hex colors or JSON array string")
    ],
    tolerance_percentage: Annotated[float, Form(ge=0, le=100)] = 10.0,
    check_logo_presence: Annotated[bool, Form()] = False,
    logo_reference_url: Annotated[str | None, Form()] = None,
    generate_heatmap: Annotated[bool, Form(description="Generate heatmap overlay")] = False,
) -> BrandValidationResponse:
    """
    Validate an image against brand guidelines.

    Args:
        image: The image file to validate.
        current_user: The authenticated user.
        brand_service: The brand validation service.
        brand_colors: Comma-separated list of brand colors in hex format or JSON array string.
        tolerance_percentage: Color matching tolerance (0-100).
        check_logo_presence: Whether to check for logo presence.
        logo_reference_url: URL to reference logo for comparison.
        generate_heatmap: Whether to generate a heatmap overlay image.

    Returns:
        BrandValidationResponse with validation results.
    """
    # Validate file
    await validate_image_file(image)

    # Parse brand colors - handle both comma-separated and JSON array formats
    import json

    logger.info(f"Received brand_colors: {brand_colors}")

    # Strip surrounding quotes if present (form data sometimes includes them)
    clean_brand_colors = brand_colors.strip().strip('"').strip("'")

    parsed_colors = None
    try:
        # Try parsing as JSON array first
        maybe_parsed = json.loads(clean_brand_colors)
        # Only use JSON result if it's actually a list
        if isinstance(maybe_parsed, list):
            parsed_colors = maybe_parsed
    except json.JSONDecodeError:
        pass

    # Fall back to comma-separated string
    if parsed_colors is None:
        parsed_colors = [c.strip() for c in clean_brand_colors.split(",")]

    logger.info(f"Parsed brand_colors: {parsed_colors}")

    # Create request model
    request = BrandValidateImageRequest(
        brand_colors=parsed_colors,
        tolerance_percentage=tolerance_percentage,
        check_logo_presence=check_logo_presence,
        logo_reference_url=logo_reference_url,
        generate_heatmap=generate_heatmap,
        additional_rules=None,
    )

    logger.info(f"Brand validation requested by user {current_user.id}")

    response = await brand_service.validate_image(
        image=image,
        request=request,
        user_id=current_user.id,
    )

    return response


@router.post(
    "/extract-colors",
    response_model=ExtractedColorsResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract colors from image",
    description="""
    Extract dominant colors from an uploaded image.

    This endpoint analyzes an image and extracts the most prominent colors,
    including their percentages and pixel counts. Useful for brand color
    analysis and palette generation.
    """,
    responses={
        200: {
            "description": "Successful color extraction",
        },
    },
)
async def extract_colors(
    image: Annotated[UploadFile, File(description="Image file to analyze")],
    current_user: Annotated[User, Depends(get_current_user)],
    brand_service: Annotated[BrandService, Depends(get_brand_service_dep)],
    max_colors: Annotated[int, Form(ge=1, le=20)] = 5,
    include_percentages: Annotated[bool, Form()] = True,
    group_similar: Annotated[bool, Form()] = True,
    similarity_threshold: Annotated[float, Form(ge=0, le=100)] = 15.0,
) -> ExtractedColorsResponse:
    """
    Extract dominant colors from an image.

    Args:
        image: The image file to analyze.
        current_user: The authenticated user.
        brand_service: The brand service.
        max_colors: Maximum number of colors to extract (1-20).
        include_percentages: Whether to include color percentages.
        group_similar: Whether to group similar colors.
        similarity_threshold: Threshold for grouping similar colors.

    Returns:
        ExtractedColorsResponse with extracted color palette.
    """
    # TODO: Implement color extraction
    # - Validate uploaded file
    # - Call brand service for extraction
    # - Return extracted colors

    # Validate file
    await validate_image_file(image)

    request = BrandExtractColorsRequest(
        max_colors=max_colors,
        include_percentages=include_percentages,
        group_similar=group_similar,
        similarity_threshold=similarity_threshold,
    )

    logger.info(f"Color extraction requested by user {current_user.id}")

    response = await brand_service.extract_colors(
        image=image,
        request=request,
        user_id=current_user.id,
    )

    return response


@router.post(
    "/compare-images",
    response_model=ImageComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare two images",
    description="""
    Compare two images for brand consistency.

    This endpoint analyzes two images and compares them for:
    - Overall visual similarity
    - Color palette similarity
    - Layout similarity (optional)
    - Specific differences between the images
    """,
    responses={
        200: {
            "description": "Successful image comparison",
        },
    },
)
async def compare_images(
    image1: Annotated[UploadFile, File(description="First image file")],
    image2: Annotated[UploadFile, File(description="Second image file")],
    current_user: Annotated[User, Depends(get_current_user)],
    brand_service: Annotated[BrandService, Depends(get_brand_service_dep)],
    comparison_type: Annotated[str, Form()] = "visual",
    include_color_diff: Annotated[bool, Form()] = True,
    include_layout_diff: Annotated[bool, Form()] = False,
    sensitivity: Annotated[float, Form(ge=0, le=1)] = 0.9,
) -> ImageComparisonResponse:
    """
    Compare two images for brand consistency.

    Args:
        image1: First image file.
        image2: Second image file.
        current_user: The authenticated user.
        brand_service: The brand service.
        comparison_type: Type of comparison (visual, colors, layout).
        include_color_diff: Whether to include color difference analysis.
        include_layout_diff: Whether to include layout difference analysis.
        sensitivity: Comparison sensitivity (0-1).

    Returns:
        ImageComparisonResponse with comparison results.
    """
    # TODO: Implement image comparison
    # - Validate both uploaded files
    # - Call brand service for comparison
    # - Return comparison results

    # Validate files
    await validate_image_file(image1)
    await validate_image_file(image2)

    request = BrandCompareImagesRequest(
        comparison_type=comparison_type,
        include_color_diff=include_color_diff,
        include_layout_diff=include_layout_diff,
        sensitivity=sensitivity,
    )

    logger.info(f"Image comparison requested by user {current_user.id}")

    response = await brand_service.compare_images(
        image1=image1,
        image2=image2,
        request=request,
        user_id=current_user.id,
    )

    return response
