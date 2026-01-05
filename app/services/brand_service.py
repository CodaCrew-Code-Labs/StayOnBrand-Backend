"""
Brand validation and color extraction service.
"""

import logging
import uuid
from datetime import datetime

import cv2
import numpy as np
from fastapi import UploadFile

from app.models.common import Color, ImageMetadata
from app.models.enums import BrandComplianceLevel
from app.models.requests import (
    BrandCompareImagesRequest,
    BrandExtractColorsRequest,
    BrandValidateImageRequest,
)
from app.models.responses import (
    BrandValidationResponse,
    DetectedColorMatch,
    ExtractedColor,
    ExtractedColorsResponse,
    ImageComparisonResponse,
    ImageDifference,
)
from app.scripts.BrandColorAlignment import BrandColorAnalyzer, BrandColorSpec
from app.services.redis_service import RedisService

logger = logging.getLogger(__name__)


class BrandService:
    """
    Service for brand validation and image analysis.

    Provides methods for:
    - Validating images against brand guidelines
    - Extracting dominant colors from images
    - Comparing images for brand consistency
    """

    def __init__(self, redis_service: RedisService | None = None):
        """
        Initialize brand service.

        Args:
            redis_service: Redis service for caching.
        """
        self._redis = redis_service
        self._color_analyzer = BrandColorAnalyzer()

    async def validate_image(
        self,
        image: UploadFile,
        request: BrandValidateImageRequest,
        user_id: str,
    ) -> BrandValidationResponse:
        """
        Validate an image against brand guidelines.

        Args:
            image: The uploaded image file.
            request: Validation parameters.
            user_id: ID of the user making the request.

        Returns:
            BrandValidationResponse with validation results.
        """
        validation_id = str(uuid.uuid4())

        image_metadata = await self._extract_image_metadata(image)

        # Analyze brand colors using BrandColorAnalyzer
        top_color_matches, alignment_score, heatmap_base64 = await self._analyze_brand_colors(
            image,
            request.brand_colors,
            generate_heatmap=request.generate_heatmap,
        )

        compliance_score = alignment_score
        compliance_level = self._determine_compliance_level(compliance_score)

        # Cache the result
        if self._redis:
            await self._cache_validation_result(
                validation_id,
                user_id,
                "brand_image",
                compliance_score,
            )

        return BrandValidationResponse(
            success=True,
            message="Brand validation completed",
            validation_id=validation_id,
            brand_color_match=f"Brand color match: {int(round(compliance_score))}%",
            compliance_score=compliance_score,
            compliance_level=compliance_level,
            top_color_matches=top_color_matches,
            heatmap_image=heatmap_base64,
            image_metadata=image_metadata,
            processed_at=datetime.utcnow(),
        )

    async def extract_colors(
        self,
        image: UploadFile,
        request: BrandExtractColorsRequest,
        user_id: str,
    ) -> ExtractedColorsResponse:
        """
        Extract dominant colors from an image.

        Args:
            image: The uploaded image file.
            request: Extraction parameters.
            user_id: ID of the user making the request.

        Returns:
            ExtractedColorsResponse with extracted colors.
        """
        # TODO: Implement color extraction logic
        # - Load image data
        # - Quantize colors (k-means or similar)
        # - Group similar colors if requested
        # - Calculate percentages and pixel counts
        # - Identify dominant color
        # - Detect palette type (complementary, analogous, etc.)

        validation_id = str(uuid.uuid4())

        # TODO: Extract actual image metadata
        image_metadata = await self._extract_image_metadata(image)

        # TODO: Implement actual color extraction
        colors = await self._extract_colors_from_image(
            image,
            request.max_colors,
            request.group_similar,
            request.similarity_threshold,
        )

        # TODO: Identify dominant color
        dominant_color = (
            colors[0].color
            if colors
            else Color(
                hex="#000000",
                rgb={"r": 0, "g": 0, "b": 0},
                hsl={"h": 0, "s": 0, "l": 0},
                name="black",
            )
        )

        # TODO: Detect palette type
        palette_type = await self._detect_palette_type(colors)

        return ExtractedColorsResponse(
            success=True,
            message="Color extraction completed",
            validation_id=validation_id,
            colors=colors,
            total_colors_found=len(colors),
            dominant_color=dominant_color,
            palette_type=palette_type,
            image_metadata=image_metadata,
        )

    async def compare_images(
        self,
        image1: UploadFile,
        image2: UploadFile,
        request: BrandCompareImagesRequest,
        user_id: str,
    ) -> ImageComparisonResponse:
        """
        Compare two images for brand consistency.

        Args:
            image1: First image file.
            image2: Second image file.
            request: Comparison parameters.
            user_id: ID of the user making the request.

        Returns:
            ImageComparisonResponse with comparison results.
        """
        # TODO: Implement image comparison logic
        # - Load both images
        # - Compare visual similarity
        # - Compare color palettes
        # - Compare layouts if requested
        # - Identify and locate differences

        validation_id = str(uuid.uuid4())

        # TODO: Extract metadata for both images
        image1_metadata = await self._extract_image_metadata(image1)
        image2_metadata = await self._extract_image_metadata(image2)

        # TODO: Implement actual comparison
        similarity_score = await self._calculate_similarity(
            image1,
            image2,
            request.sensitivity,
        )

        color_similarity = await self._compare_color_palettes(image1, image2)

        layout_similarity = None
        if request.include_layout_diff:
            layout_similarity = await self._compare_layouts(image1, image2)

        differences = await self._find_differences(
            image1,
            image2,
            request,
        )

        return ImageComparisonResponse(
            success=True,
            message="Image comparison completed",
            validation_id=validation_id,
            similarity_score=similarity_score,
            are_identical=similarity_score >= 99.9,
            color_similarity=color_similarity,
            layout_similarity=layout_similarity,
            differences=differences,
            image1_metadata=image1_metadata,
            image2_metadata=image2_metadata,
        )

    async def _extract_image_metadata(self, image: UploadFile) -> ImageMetadata:
        """
        Extract metadata from uploaded image.

        Args:
            image: The uploaded image file.

        Returns:
            ImageMetadata object.
        """
        content = await image.read()
        await image.seek(0)  # Reset for further processing

        # Decode image to get dimensions
        nparr = np.frombuffer(content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        width = None
        height = None
        if img is not None:
            height, width = img.shape[:2]

        return ImageMetadata(
            filename=image.filename or "unknown",
            size_bytes=len(content),
            width=width,
            height=height,
            format=image.filename.split(".")[-1] if image.filename else "unknown",
            mime_type=image.content_type or "application/octet-stream",
        )

    async def _read_image_as_bgr(self, image: UploadFile) -> np.ndarray:
        """
        Read an uploaded image file as BGR numpy array.

        Args:
            image: The uploaded image file.

        Returns:
            BGR numpy array.
        """
        content = await image.read()
        await image.seek(0)
        nparr = np.frombuffer(content, np.uint8)
        bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError("Failed to decode image")
        return bgr

    def _hex_to_color_name(self, hex_color: str) -> str:
        """
        Convert hex color to a human-readable color name.

        Uses a simple heuristic based on RGB values.
        """
        hex_clean = hex_color.lstrip("#")
        r = int(hex_clean[0:2], 16)
        g = int(hex_clean[2:4], 16)
        b = int(hex_clean[4:6], 16)

        # Calculate brightness and saturation-like values
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        brightness = (max_c + min_c) / 2

        # Check for grayscale first
        if max_c - min_c < 30:
            if brightness > 220:
                return "white"
            elif brightness > 160:
                return "light gray"
            elif brightness > 80:
                return "gray"
            elif brightness > 30:
                return "dark gray"
            else:
                return "black"

        # Determine dominant color
        if r >= g and r >= b:
            if g > b + 30:
                return "orange" if r > 200 and g > 100 else "brown"
            elif b > g + 30:
                return "pink" if brightness > 150 else "magenta"
            else:
                return "red"
        elif g >= r and g >= b:
            if b > r + 30:
                return "teal" if b > 100 else "cyan"
            elif r > b + 30:
                return "yellow" if r > 180 else "olive"
            else:
                return "green"
        else:  # b is dominant
            if r > g + 30:
                return "purple" if r > 100 else "violet"
            elif g > r + 30:
                return "cyan" if g > 150 else "teal"
            else:
                return "blue"

    async def _analyze_brand_colors(
        self,
        image: UploadFile,
        brand_colors: list[str],
        generate_heatmap: bool = False,
    ) -> tuple[list[DetectedColorMatch], float, str | None]:
        """
        Analyze image colors against brand colors using BrandColorAnalyzer.

        Args:
            image: The uploaded image.
            brand_colors: List of brand colors in hex.
            generate_heatmap: Whether to generate a heatmap overlay.

        Returns:
            Tuple of (list of DetectedColorMatch objects, alignment_score, heatmap_base64 or None).
        """
        if not brand_colors:
            return [], 0.0, None

        # Read image as BGR
        bgr = await self._read_image_as_bgr(image)

        # Convert brand colors to BrandColorSpec
        brand_specs = [BrandColorSpec(hex=color) for color in brand_colors]

        # Analyze using BrandColorAnalyzer
        result = self._color_analyzer.analyze(
            bgr_image=bgr,
            brand_colors=brand_specs,
            k_clusters=8,
            generate_heatmap=generate_heatmap,
        )

        alignment_score = result["alignment_score"]
        top_detected = result.get("top_detected_colors", [])
        heatmap_base64 = result.get("heatmap_base64")

        # Convert to DetectedColorMatch objects
        matches = []
        for item in top_detected:
            detected_hex = item["detected_color"]
            brand_hex = item["nearest_brand_color"]
            match_pct = item["match_percentage"]
            coverage_pct = item["coverage_percentage"]

            detected_name = self._hex_to_color_name(detected_hex)
            brand_name = self._hex_to_color_name(brand_hex)

            # Build human-readable description
            if match_pct >= 90:
                description = (
                    f"This {detected_name} matches brand {brand_name}: {int(match_pct)}% match"
                )
            elif match_pct >= 70:
                description = (
                    f"This {detected_name} is close to brand {brand_name}: {int(match_pct)}% match"
                )
            else:
                description = (
                    f"This {detected_name} differs from brand {brand_name}: {int(match_pct)}% match"
                )

            matches.append(
                DetectedColorMatch(
                    detected_color=detected_hex,
                    detected_color_name=detected_name,
                    nearest_brand_color=brand_hex,
                    match_percentage=match_pct,
                    coverage_percentage=coverage_pct,
                    description=description,
                )
            )

        return matches, alignment_score, heatmap_base64

    def _determine_compliance_level(self, score: float) -> BrandComplianceLevel:
        """
        Determine compliance level from score.

        Args:
            score: Compliance score (0-100).

        Returns:
            BrandComplianceLevel enum value.
        """
        # TODO: Implement thresholds
        if score >= 80:
            return BrandComplianceLevel.COMPLIANT
        elif score >= 50:
            return BrandComplianceLevel.PARTIAL
        else:
            return BrandComplianceLevel.NON_COMPLIANT

    async def _extract_colors_from_image(
        self,
        image: UploadFile,
        max_colors: int,
        group_similar: bool,
        similarity_threshold: float,
    ) -> list[ExtractedColor]:
        """
        Extract colors from image.

        Args:
            image: The uploaded image.
            max_colors: Maximum colors to extract.
            group_similar: Whether to group similar colors.
            similarity_threshold: Threshold for grouping.

        Returns:
            List of ExtractedColor objects.
        """
        # TODO: Implement color extraction
        # - Use k-means clustering or similar
        # - Group similar colors if requested
        # - Calculate percentages

        return []

    async def _detect_palette_type(
        self,
        colors: list[ExtractedColor],
    ) -> str:
        """
        Detect the color palette type.

        Args:
            colors: Extracted colors.

        Returns:
            Palette type string.
        """
        # TODO: Implement palette detection
        # - Analyze color relationships
        # - Detect complementary, analogous, triadic, etc.
        return "unknown"

    async def _calculate_similarity(
        self,
        image1: UploadFile,
        image2: UploadFile,
        sensitivity: float,
    ) -> float:
        """
        Calculate visual similarity between images.

        Args:
            image1: First image.
            image2: Second image.
            sensitivity: Comparison sensitivity.

        Returns:
            Similarity score (0-100).
        """
        # TODO: Implement similarity calculation
        # - Use perceptual hashing or similar
        # - Compare histograms
        # - Consider structural similarity
        return 0.0

    async def _compare_color_palettes(
        self,
        image1: UploadFile,
        image2: UploadFile,
    ) -> float:
        """
        Compare color palettes of two images.

        Args:
            image1: First image.
            image2: Second image.

        Returns:
            Color similarity score (0-100).
        """
        # TODO: Implement color palette comparison
        return 0.0

    async def _compare_layouts(
        self,
        image1: UploadFile,
        image2: UploadFile,
    ) -> float:
        """
        Compare layouts of two images.

        Args:
            image1: First image.
            image2: Second image.

        Returns:
            Layout similarity score (0-100).
        """
        # TODO: Implement layout comparison
        return 0.0

    async def _find_differences(
        self,
        image1: UploadFile,
        image2: UploadFile,
        request: BrandCompareImagesRequest,
    ) -> list[ImageDifference]:
        """
        Find differences between two images.

        Args:
            image1: First image.
            image2: Second image.
            request: Comparison parameters.

        Returns:
            List of ImageDifference objects.
        """
        # TODO: Implement difference detection
        # - Find color differences
        # - Find layout differences
        # - Locate and describe differences
        return []

    async def _cache_validation_result(
        self,
        validation_id: str,
        user_id: str,
        validation_type: str,
        score: float,
    ) -> None:
        """Cache validation result for history."""
        # TODO: Implement caching
        if self._redis:
            await self._redis.set(
                f"validation:{validation_id}",
                {
                    "user_id": user_id,
                    "type": validation_type,
                    "score": score,
                    "created_at": datetime.utcnow().isoformat(),
                },
            )


# Factory function
def get_brand_service(redis_service: RedisService | None = None) -> BrandService:
    """Get brand service instance."""
    return BrandService(redis_service)
