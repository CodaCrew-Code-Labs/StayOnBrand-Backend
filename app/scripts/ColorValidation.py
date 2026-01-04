import re
from typing import Any


class ColorValidation:
    """Color validation class for validating color lists."""

    def colorContrastValidation(self, colors: list[str]) -> dict[str, dict[str, Any]]:
        """
        Validate a list of colors.

        Args:
            colors: List of color strings (min 2, max 5)

        Returns:
            Dict with color pair comparisons and WCAG validation results

        Raises:
            ValueError: If list length is not between 2 and 5
        """
        if not isinstance(colors, list):
            raise ValueError("Input must be a list")

        if not 2 <= len(colors) <= 5:
            raise ValueError("Color list must contain between 2 and 5 colors")

        # Validate color codes
        validated_colors = []
        for color in colors:
            if not isinstance(color, str):
                raise ValueError("All colors must be strings")
            validated_color = self._colorCodeValidation(color.strip())
            validated_colors.append(validated_color)

        # Check if validated colors differ from input
        normalized_input = [color.strip().upper() for color in colors]
        if validated_colors != normalized_input:
            raise ValueError("Color codes are not compatible - validation failed")

        # Compare each color against each other
        comparisons = {}
        for i in range(len(validated_colors)):
            for j in range(i + 1, len(validated_colors)):
                color_a = validated_colors[i]
                color_b = validated_colors[j]
                key = f"{color_a}_{color_b}"
                comparisons[key] = self._wcagValidation(color_a, color_b)

        return comparisons

    def _colorCodeValidation(self, color: str) -> str:
        """Private method to validate color code format.

        Args:
            color: Color string to validate

        Returns:
            Validated color string

        Raises:
            ValueError: If color format is invalid
        """
        if not color.startswith("#"):
            raise ValueError(f"Invalid color format: {color}. Must start with #")

        if len(color) != 7:
            raise ValueError(f"Invalid color format: {color}. Must be 7 characters (#RRGGBB)")

        if not re.match(r"^#[0-9A-Fa-f]{6}$", color):
            raise ValueError(f"Invalid color format: {color}. Must contain valid hex characters")

        return color.upper()

    def _wcagValidation(self, color1: str, color2: str) -> dict[str, Any]:
        """Private method to validate WCAG contrast between two colors.

        Args:
            color1: First color (hex format)
            color2: Second color (hex format)

        Returns:
            Dict with comprehensive contrast validation results
        """
        # Calculate luminance for both colors
        lum1 = self._calculateLuminance(color1)
        lum2 = self._calculateLuminance(color2)

        # Calculate contrast ratio
        contrast_ratio = (max(lum1, lum2) + 0.05) / (min(lum1, lum2) + 0.05)

        # APCA score calculation
        apca_score = self._calculateAPCA(lum1, lum2)

        return {
            "luminance": {"foreground": round(lum1, 3), "background": round(lum2, 3)},
            "contrast_ratio": f"{contrast_ratio:.1f}:1",
            "wcag": {
                "A": {
                    "text": "pass" if contrast_ratio >= 3.0 else "fail",
                    "large_text": "pass" if contrast_ratio >= 3.0 else "fail",
                    "ui_icons": "pass" if contrast_ratio >= 3.0 else "fail",
                },
                "AA": {
                    "text": "pass" if contrast_ratio >= 4.5 else "fail",
                    "large_text": "pass" if contrast_ratio >= 3.0 else "fail",
                    "ui_icons": "pass" if contrast_ratio >= 3.0 else "fail",
                },
                "AAA": {
                    "text": "pass" if contrast_ratio >= 7.0 else "fail",
                    "large_text": "pass" if contrast_ratio >= 4.5 else "fail",
                    "ui_icons": "pass" if contrast_ratio >= 3.0 else "fail",
                },
            },
            "apca": {"score": apca_score, "rating": self._getAPCARating(apca_score)},
            "auto_fixes": self._generateAutoFixes(color1, color2, contrast_ratio),
            "color_blind_risk": self._assessColorBlindRisk(color1, color2),
        }

    def _calculateLuminance(self, color: str) -> float:
        """Calculate relative luminance of a color.

        Args:
            color: Hex color string

        Returns:
            Relative luminance value
        """
        # Convert hex to RGB
        r = int(color[1:3], 16) / 255.0
        g = int(color[3:5], 16) / 255.0
        b = int(color[5:7], 16) / 255.0

        # Apply gamma correction
        def gamma_correct(c: float) -> float:
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

        r = gamma_correct(r)
        g = gamma_correct(g)
        b = gamma_correct(b)

        # Calculate luminance
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def _calculateAPCA(self, lum1: float, lum2: float) -> int:
        """Calculate APCA contrast score."""
        # Simplified APCA calculation
        y_txt = lum1 if lum1 > lum2 else lum2
        y_bg = lum2 if lum1 > lum2 else lum1

        if y_bg < 0.022:
            y_bg += 0.022 - y_bg
        if y_txt < 0.022:
            y_txt += 0.022 - y_txt

        apca = (y_txt**0.56 - y_bg**0.57) * 1.14
        return int(apca * 100)

    def _getAPCARating(self, score: int) -> str:
        """Get APCA rating based on score."""
        abs_score = abs(score)
        if abs_score >= 90:
            return "excellent"
        elif abs_score >= 75:
            return "very good"
        elif abs_score >= 60:
            return "good"
        elif abs_score >= 45:
            return "fair"
        else:
            return "poor"

    def _generateAutoFixes(self, color1: str, color2: str, ratio: float) -> dict[str, str]:
        """Generate auto-fix suggestions."""
        fixes = {}
        if ratio < 7.0:  # Need AAA compliance
            # Darken foreground for better contrast
            r, g, b = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
            factor = 0.7
            fixes["foreground_to_meet_AAA"] = (
                f"#{int(r*factor):02X}{int(g*factor):02X}{int(b*factor):02X}"
            )

            # Lighten background
            r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
            factor2 = 1.2
            fixes["background_variant_for_better_accessibility"] = (
                f"#{min(255, int(r2*factor2)):02X}{min(255, int(g2*factor2)):02X}{min(255, int(b2*factor2)):02X}"
            )

        return fixes

    def _assessColorBlindRisk(self, color1: str, color2: str) -> str:
        """Assess color blindness risk."""
        # Convert to RGB
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)

        # Calculate color difference
        red_diff = abs(r1 - r2)
        green_diff = abs(g1 - g2)
        blue_diff = abs(b1 - b2)

        total_diff = red_diff + green_diff + blue_diff

        if total_diff > 400:
            return "low"
        elif total_diff > 200:
            return "medium"
        else:
            return "high"