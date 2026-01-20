"""
Color contrast comparison endpoints.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dependencies import get_current_user
from app.models.common import User
from app.models.requests import ColorCompareRequest
from app.models.responses import ColorCompareResponse
from app.scripts.ColorValidation import ColorValidation

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/colors",
    tags=["Color Contrast"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing authentication"},
        422: {"description": "Validation Error"},
        500: {"description": "Internal Server Error"},
    },
)


@router.post(
    "/compare",
    response_model=ColorCompareResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare multiple colors contrast",
    description="""
    Compare contrast ratios between multiple colors (2-5) and check WCAG compliance.

    This endpoint validates and compares all color pairs, calculating contrast ratios,
    determining WCAG compliance levels (A/AA/AAA for text, large text, and UI icons),
    and provides comprehensive accessibility analysis including APCA scores and auto-fixes.
    """,
    responses={
        200: {
            "description": "Successful color comparison",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Color comparison completed successfully",
                        "colors": ["#FFFFFF", "#000000"],
                        "comparisons": {
                            "#FFFFFF_#000000": {
                                "luminance": {"foreground": 1.0, "background": 0.0},
                                "contrast_ratio": "21.0:1",
                                "wcag": {
                                    "A": {"text": "pass", "large_text": "pass", "ui_icons": "pass"},
                                    "AA": {
                                        "text": "pass",
                                        "large_text": "pass",
                                        "ui_icons": "pass",
                                    },
                                    "AAA": {
                                        "text": "pass",
                                        "large_text": "pass",
                                        "ui_icons": "pass",
                                    },
                                },
                            }
                        },
                    }
                }
            },
        },
    },
)
async def compare_colors(
    request: ColorCompareRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> ColorCompareResponse:
    """
    Compare multiple colors for contrast ratio and WCAG compliance.

    Args:
        request: Color comparison parameters with list of colors (2-5).
        current_user: The authenticated user making the request.

    Returns:
        ColorCompareResponse with all color pair comparisons and WCAG validation.
    """
    logger.info(
        f"Color comparison requested by user {current_user.id}: "
        f"{len(request.colors)} colors - {request.colors}"
    )

    # Use ColorValidation class to get comprehensive results
    color_validator = ColorValidation()
    comparisons = color_validator.colorContrastValidation(request.colors)
    color_scores, palette_score = color_validator.calculateScores(request.colors, comparisons)

    return ColorCompareResponse(
        success=True,
        message="Color comparison completed successfully",
        colors=request.colors,
        comparisons=comparisons,
        color_scores=color_scores,
        palette_score=palette_score,
    )
