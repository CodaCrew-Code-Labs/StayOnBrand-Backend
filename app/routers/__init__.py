"""
API routers for the StayOnBoard application.
"""

from app.routers.brand import router as brand_router
from app.routers.colors import router as colors_router
from app.routers.utils import router as utils_router
from app.routers.validate import router as validate_router
from app.routers.wcag import router as wcag_router

__all__ = [
    "brand_router",
    "colors_router",
    "utils_router",
    "validate_router",
    "wcag_router",
]
