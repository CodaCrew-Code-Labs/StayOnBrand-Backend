"""
WCAG accessibility validation service.
"""

import logging
import uuid
from datetime import datetime

from fastapi import UploadFile

from app.models.common import BoundingBox, ImageMetadata
from app.models.enums import TextSize, WCAGLevel, WCAGVersion
from app.models.requests import WCAGValidateImageRequest, WCAGValidateTextContrastRequest
from app.models.responses import (
    WCAGCriterion,
    WCAGIssue,
    WCAGRequirementsResponse,
    WCAGTextContrastResponse,
    WCAGValidationResponse,
)
from app.scripts.ImageA11yEvalution import evaluate_image_accessibility_from_bytes
from app.services.color_service import ColorService
from app.services.redis_service import RedisService

logger = logging.getLogger(__name__)


class WCAGService:
    """
    Service for WCAG accessibility validation.

    Provides methods for:
    - Validating images for WCAG compliance
    - Checking text contrast requirements
    - Listing WCAG requirements and criteria
    """

    # WCAG Criteria definitions
    WCAG_CRITERIA = {
        "1.4.3": {
            "title": "Contrast (Minimum)",
            "level": WCAGLevel.AA,
            "description": "Text and images of text have a contrast ratio of at least 4.5:1",
        },
        "1.4.6": {
            "title": "Contrast (Enhanced)",
            "level": WCAGLevel.AAA,
            "description": "Text and images of text have a contrast ratio of at least 7:1",
        },
        "1.4.11": {
            "title": "Non-text Contrast",
            "level": WCAGLevel.AA,
            "description": "UI components and graphical objects have contrast ratio of at least 3:1",
        },
    }

    def __init__(
        self,
        color_service: ColorService | None = None,
        redis_service: RedisService | None = None,
    ):
        """
        Initialize WCAG service.

        Args:
            color_service: Color service for contrast calculations.
            redis_service: Redis service for caching.
        """
        self._color_service = color_service or ColorService()
        self._redis = redis_service

    async def validate_image(
        self,
        image: UploadFile,
        request: WCAGValidateImageRequest,
        user_id: str,
    ) -> WCAGValidationResponse:
        """
        Validate an image for WCAG compliance.

        Args:
            image: The uploaded image file.
            request: Validation parameters.
            user_id: ID of the user making the request.

        Returns:
            WCAGValidationResponse with validation results.
        """
        validation_id = str(uuid.uuid4())

        # Extract image metadata
        image_metadata = await self._extract_image_metadata(image)

        # Detect issues using the accessibility evaluation script
        issues, eval_result = await self._detect_wcag_issues(image, request)

        # Determine passed criteria
        passed_criteria = self._get_passed_criteria(issues, request.wcag_level)

        # Generate suggestions based on issues and include notes from eval
        suggestions = self._generate_suggestions(issues)
        if request.include_suggestions:
            suggestions.extend(eval_result.get("notes", []))

        # Use the overall score from the evaluation script
        compliance_score = eval_result.get("overall_score", 100.0)

        # Determine achieved level and compliance
        # AA = compliant (no A-level issues)
        # AAA = super compliant (no A or AA-level issues)
        wcag_level_achieved = self._determine_achieved_level(issues)

        # Check compliance: AA is compliant if achieved level >= AA, AAA is super compliant
        # A-level issues make it non-compliant for any target
        # AA-level issues make it non-compliant only for AAA target
        a_level_issues = [i for i in issues if i.level == WCAGLevel.A]
        aa_level_issues = [i for i in issues if i.level == WCAGLevel.AA]

        if request.wcag_level == WCAGLevel.AAA:
            # For AAA target: compliant if no A or AA issues
            is_compliant = len(a_level_issues) == 0 and len(aa_level_issues) == 0
        elif request.wcag_level == WCAGLevel.AA:
            # For AA target: compliant if no A-level issues (AA issues are acceptable)
            is_compliant = len(a_level_issues) == 0
        else:
            # For A target: compliant if no A-level issues
            is_compliant = len(a_level_issues) == 0

        # Cache result
        if self._redis:
            await self._cache_validation_result(
                validation_id,
                user_id,
                "wcag_image",
                compliance_score,
            )

        return WCAGValidationResponse(
            success=True,
            message="WCAG validation completed",
            validation_id=validation_id,
            is_compliant=is_compliant,
            compliance_score=compliance_score,
            wcag_level_achieved=wcag_level_achieved,
            issues=issues,
            passed_criteria=passed_criteria,
            suggestions=suggestions,
            image_metadata=image_metadata,
            processed_at=datetime.utcnow(),
        )

    async def validate_text_contrast(
        self,
        request: WCAGValidateTextContrastRequest,
        user_id: str,
    ) -> WCAGTextContrastResponse:
        """
        Validate text contrast against WCAG requirements.

        Args:
            request: Contrast validation parameters.
            user_id: ID of the user making the request.

        Returns:
            WCAGTextContrastResponse with validation results.
        """
        # TODO: Implement text contrast validation
        # - Calculate contrast ratio
        # - Determine text size category
        # - Check against AA and AAA requirements
        # - Generate recommendations if non-compliant

        validation_id = str(uuid.uuid4())

        # Calculate contrast ratio
        contrast_ratio = self._color_service.calculate_contrast_ratio(
            request.foreground_color,
            request.background_color,
        )

        # Determine text size category
        text_size_category = self._determine_text_size_category(
            request.text_size_px,
            request.is_bold,
        )

        # Determine requirements based on text size
        if text_size_category == "large":
            aa_required = 3.0
            aaa_required = 4.5
        else:
            aa_required = 4.5
            aaa_required = 7.0

        # Check compliance
        passes_aa = contrast_ratio >= aa_required
        passes_aaa = contrast_ratio >= aaa_required

        # Determine if compliant for requested level
        required_ratio = aaa_required if request.wcag_level == WCAGLevel.AAA else aa_required
        is_compliant = contrast_ratio >= required_ratio

        # Generate recommendations if non-compliant
        recommendations = None
        if not is_compliant:
            recommendations = self._color_service.generate_recommendations(
                request.foreground_color,
                request.background_color,
                request.wcag_level,
                TextSize.LARGE if text_size_category == "large" else TextSize.NORMAL,
            )

        # Cache result
        if self._redis:
            await self._cache_validation_result(
                validation_id,
                user_id,
                "wcag_text_contrast",
                100.0 if is_compliant else 0.0,
            )

        return WCAGTextContrastResponse(
            success=True,
            message="Text contrast validation completed",
            validation_id=validation_id,
            contrast_ratio=round(contrast_ratio, 2),
            is_compliant=is_compliant,
            required_ratio=required_ratio,
            wcag_level=request.wcag_level,
            text_size_category=text_size_category,
            passes_aa=passes_aa,
            passes_aaa=passes_aaa,
            recommendations=recommendations,
        )

    def get_requirements(
        self,
        version: WCAGVersion = WCAGVersion.WCAG_21,
        level: WCAGLevel | None = None,
    ) -> WCAGRequirementsResponse:
        """
        Get WCAG requirements and criteria.

        Args:
            version: WCAG version to get requirements for.
            level: Optional filter by conformance level.

        Returns:
            WCAGRequirementsResponse with criteria list.
        """
        # TODO: Implement comprehensive WCAG criteria listing
        # - Load criteria definitions for version
        # - Filter by level if specified
        # - Include how-to-meet guidance
        # - Include sufficient techniques

        criteria = self._get_criteria_for_version(version, level)

        level_a_count = sum(1 for c in criteria if c.level == WCAGLevel.A)
        level_aa_count = sum(1 for c in criteria if c.level == WCAGLevel.AA)
        level_aaa_count = sum(1 for c in criteria if c.level == WCAGLevel.AAA)

        return WCAGRequirementsResponse(
            success=True,
            message="WCAG requirements retrieved",
            version=version.value,
            criteria=criteria,
            total_level_a=level_a_count,
            total_level_aa=level_aa_count,
            total_level_aaa=level_aaa_count,
        )

    async def _extract_image_metadata(self, image: UploadFile) -> ImageMetadata:
        """Extract metadata from uploaded image."""
        # TODO: Implement metadata extraction
        content = await image.read()
        await image.seek(0)

        return ImageMetadata(
            filename=image.filename or "unknown",
            size_bytes=len(content),
            width=None,
            height=None,
            format=image.filename.split(".")[-1] if image.filename else "unknown",
            mime_type=image.content_type or "application/octet-stream",
        )

    async def _detect_wcag_issues(
        self,
        image: UploadFile,
        request: WCAGValidateImageRequest,
    ) -> tuple[list[WCAGIssue], dict]:
        """
        Detect WCAG issues in an image using the ImageA11yEvalution script.

        Args:
            image: The uploaded image.
            request: Validation parameters.

        Returns:
            Tuple of (list of WCAGIssue objects, raw evaluation result dict).
        """
        issues: list[WCAGIssue] = []

        # Read image bytes
        content = await image.read()
        await image.seek(0)

        # Run accessibility evaluation
        eval_result = evaluate_image_accessibility_from_bytes(content)

        # Convert regions with issues to WCAGIssue objects
        if request.check_color_contrast:
            for region in eval_result.get("regions", []):
                # Check contrast ratio against WCAG thresholds
                threshold = 3.0 if region["is_large"] else 4.5
                if region["contrast"] < threshold:
                    bbox = region["bbox"]
                    issues.append(
                        WCAGIssue(
                            criterion="1.4.3",
                            level=WCAGLevel.AA,
                            title="Insufficient Text Contrast",
                            description=(
                                f"Text '{region['text']}' has contrast ratio of {region['contrast']:.2f}:1, "
                                f"which is below the required {threshold}:1 for "
                                f"{'large' if region['is_large'] else 'normal'} text."
                            ),
                            impact="serious",
                            location=BoundingBox(
                                x=bbox["x"],
                                y=bbox["y"],
                                width=bbox["w"],
                                height=bbox["h"],
                            ),
                            suggestion=f"Increase contrast ratio to at least {threshold}:1 by using darker text or lighter background.",
                        )
                    )

                # Check colorblind safety
                cb_threshold = 3.0 if region["is_large"] else 4.5
                if region["colorblind_min_contrast"] < cb_threshold:
                    bbox = region["bbox"]
                    issues.append(
                        WCAGIssue(
                            criterion="1.4.1",
                            level=WCAGLevel.A,
                            title="Color-blind Accessibility Issue",
                            description=(
                                f"Text '{region['text']}' may be difficult to read for color-blind users. "
                                f"Minimum contrast under color-blind simulation: {region['colorblind_min_contrast']:.2f}:1."
                            ),
                            impact="moderate",
                            location=BoundingBox(
                                x=bbox["x"],
                                y=bbox["y"],
                                width=bbox["w"],
                                height=bbox["h"],
                            ),
                            suggestion="Consider using colors that maintain sufficient contrast for users with color vision deficiencies.",
                        )
                    )

        if request.check_text_size:
            # Check for regions with small text and low legibility
            for region in eval_result.get("regions", []):
                if not region["is_large"] and region["clutter"] > 0.5:
                    bbox = region["bbox"]
                    issues.append(
                        WCAGIssue(
                            criterion="1.4.4",
                            level=WCAGLevel.AA,
                            title="Small Text in Cluttered Area",
                            description=(
                                f"Small text '{region['text']}' appears in a cluttered area "
                                f"(clutter score: {region['clutter']:.2f}), reducing legibility."
                            ),
                            impact="moderate",
                            location=BoundingBox(
                                x=bbox["x"],
                                y=bbox["y"],
                                width=bbox["w"],
                                height=bbox["h"],
                            ),
                            suggestion="Consider using larger text or reducing background complexity to improve readability.",
                        )
                    )

        return issues, eval_result

    def _get_passed_criteria(
        self,
        issues: list[WCAGIssue],
        target_level: WCAGLevel,
    ) -> list[str]:
        """
        Get list of passed WCAG criteria.

        Args:
            issues: Detected issues.
            target_level: Target WCAG level.

        Returns:
            List of passed criterion IDs.
        """
        # TODO: Implement passed criteria determination
        # - Get all criteria for target level
        # - Remove criteria with issues
        # - Return remaining criteria IDs

        failed_criteria = {issue.criterion for issue in issues}
        all_criteria = set(self.WCAG_CRITERIA.keys())
        return list(all_criteria - failed_criteria)

    def _generate_suggestions(self, issues: list[WCAGIssue]) -> list[str]:
        """
        Generate improvement suggestions based on issues.

        Args:
            issues: Detected issues.

        Returns:
            List of suggestion strings.
        """
        # TODO: Implement suggestion generation
        # - Analyze issue patterns
        # - Generate actionable suggestions
        # - Prioritize by impact

        suggestions = []
        for issue in issues:
            if issue.suggestion:
                suggestions.append(issue.suggestion)
        return suggestions

    def _calculate_compliance_score(
        self,
        issues: list[WCAGIssue],
        target_level: WCAGLevel,
    ) -> float:
        """
        Calculate WCAG compliance score.

        Args:
            issues: Detected issues.
            target_level: Target WCAG level.

        Returns:
            Compliance score (0-100).
        """
        # TODO: Implement scoring algorithm
        # - Weight issues by severity and level
        # - Calculate percentage of passed criteria
        if not issues:
            return 100.0

        # Count issues at or below target level
        relevant_issues = [
            i for i in issues if self._level_value(i.level) <= self._level_value(target_level)
        ]

        if not relevant_issues:
            return 100.0

        # Simple scoring: deduct points per issue
        score = 100.0 - (len(relevant_issues) * 10)
        return max(0.0, score)

    def _level_value(self, level: WCAGLevel) -> int:
        """Convert WCAG level to numeric value for comparison."""
        return {"A": 1, "AA": 2, "AAA": 3}.get(level.value, 0)

    def _determine_achieved_level(self, issues: list[WCAGIssue]) -> WCAGLevel:
        """
        Determine highest WCAG level achieved.

        Args:
            issues: Detected issues.

        Returns:
            Highest achieved WCAGLevel.
        """
        # TODO: Implement level determination
        # - Check if all A criteria pass
        # - Check if all AA criteria pass
        # - Check if all AAA criteria pass

        level_issues = {
            WCAGLevel.A: False,
            WCAGLevel.AA: False,
            WCAGLevel.AAA: False,
        }

        for issue in issues:
            level_issues[issue.level] = True

        if not level_issues[WCAGLevel.A]:
            if not level_issues[WCAGLevel.AA]:
                if not level_issues[WCAGLevel.AAA]:
                    return WCAGLevel.AAA
                return WCAGLevel.AA
            return WCAGLevel.A

        return WCAGLevel.A  # Minimum level

    def _determine_text_size_category(
        self,
        size_px: float | None,
        is_bold: bool,
    ) -> str:
        """
        Determine if text is considered "large" by WCAG.

        Large text is:
        - 18pt (24px) or larger
        - 14pt (18.67px) or larger if bold

        Args:
            size_px: Text size in pixels.
            is_bold: Whether text is bold.

        Returns:
            "large" or "normal".
        """
        # TODO: Implement size category determination
        if size_px is None:
            return "normal"

        if is_bold:
            return "large" if size_px >= 18.67 else "normal"
        return "large" if size_px >= 24 else "normal"

    def _get_criteria_for_version(
        self,
        version: WCAGVersion,
        level: WCAGLevel | None = None,
    ) -> list[WCAGCriterion]:
        """
        Get WCAG criteria for a specific version.

        Args:
            version: WCAG version.
            level: Optional level filter.

        Returns:
            List of WCAGCriterion objects.
        """
        # TODO: Implement comprehensive criteria database
        # - Load criteria for version
        # - Filter by level if specified
        # - Include all relevant information

        criteria = []

        for criterion_id, data in self.WCAG_CRITERIA.items():
            if level is None or data["level"] == level:
                criteria.append(
                    WCAGCriterion(
                        id=criterion_id,
                        title=data["title"],
                        level=WCAGLevel(data["level"]),
                        description=data["description"],
                        how_to_meet="See WCAG documentation",  # TODO: Add actual guidance
                        techniques=[],  # TODO: Add sufficient techniques
                    )
                )

        return criteria

    async def _cache_validation_result(
        self,
        validation_id: str,
        user_id: str,
        validation_type: str,
        score: float,
    ) -> None:
        """Cache validation result for history."""
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
def get_wcag_service(
    color_service: ColorService | None = None,
    redis_service: RedisService | None = None,
) -> WCAGService:
    """Get WCAG service instance."""
    return WCAGService(color_service, redis_service)
