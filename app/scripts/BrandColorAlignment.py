from __future__ import annotations

import base64
import math
from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np

# =========================
# Tunable constants
# =========================

MAX_IMAGE_SIDE = 512  # max side length when resizing
DEFAULT_K_CLUSTERS = 8

MAX_LAB_DISTANCE = 35.0  # max distance considered "in-range"
NEUTRAL_CHROMA_THRESHOLD = 8  # chroma below this = neutral (white/gray-ish)
NEUTRAL_PENALTY_WHEN_NO_NEUTRALS = 0.4  # down-weight neutral clusters if brand has no neutrals


# =========================
# Public types
# =========================


@dataclass
class BrandColorSpec:
    """
    Minimal brand color spec: just a hex string.

    Example:
        BrandColorSpec(hex="#123456")
    """

    hex: str


# =========================
# Internal structures
# =========================


@dataclass
class _BrandColor:
    hex: str
    lab: np.ndarray  # shape (3,) in OpenCV Lab space
    is_neutral: bool  # based on chroma


# =========================
# Helpers
# =========================


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    s = hex_str.strip().lstrip("#")
    if len(s) == 3:
        s = "".join([c * 2 for c in s])
    if len(s) != 6:
        raise ValueError(f"Invalid hex color: {hex_str}")
    if any(c not in "0123456789abcdefABCDEF" for c in s):
        raise ValueError(f"Invalid hex color: {hex_str}")
    r = int(s[0:2], 16)
    g = int(s[2:4], 16)
    b = int(s[4:6], 16)
    return r, g, b


def _rgb_to_lab_opencv(rgb: tuple[int, int, int]) -> np.ndarray:
    """Convert RGB triple (0-255) to Lab using OpenCV."""
    r, g, b = rgb
    bgr_pixel = np.array([[[b, g, r]]], dtype=np.uint8)  # OpenCV uses BGR
    lab_pixel = cv2.cvtColor(bgr_pixel, cv2.COLOR_BGR2LAB)
    return np.array(lab_pixel[0, 0], dtype=np.float32)  # shape (3,)


def _chroma_from_lab(lab: np.ndarray) -> float:
    a = float(lab[1])
    b = float(lab[2])
    return math.sqrt(a * a + b * b)


def _resize_image_keep_aspect(bgr: np.ndarray, max_side: int) -> np.ndarray:
    h, w = bgr.shape[:2]
    scale = min(1.0, float(max_side) / float(max(h, w)))
    if scale >= 0.999:
        return bgr
    new_w = int(round(w * scale))
    new_h = int(round(h * scale))
    return cv2.resize(bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)


# =========================
# Core logic
# =========================


class BrandColorAnalyzer:
    """
    Core logic: given an image (BGR np.ndarray) and a list of BrandColorSpec,
    compute a brand color alignment score and useful breakdown.

    All outputs are JSON-serializable.
    """

    def __init__(
        self,
        max_lab_distance: float = MAX_LAB_DISTANCE,
        max_image_side: int = MAX_IMAGE_SIDE,
    ):
        self.max_lab_distance = max_lab_distance
        self.max_image_side = max_image_side

    # ---------- public entry point ----------

    def analyze(
        self,
        bgr_image: np.ndarray,
        brand_colors: list[BrandColorSpec],
        k_clusters: int = DEFAULT_K_CLUSTERS,
        generate_heatmap: bool = False,
    ) -> dict[str, Any]:
        """
        :param bgr_image: OpenCV-style image in BGR, uint8 or convertible
        :param brand_colors: list of BrandColorSpec (hex only)
        :param k_clusters: k-means cluster count (3–16)
        :param generate_heatmap: if True, generate a heatmap overlay image
        :return: dict with alignment_score, brand_color_coverage, debug, heatmap_base64, etc.
        """
        if not isinstance(bgr_image, np.ndarray):
            raise TypeError("bgr_image must be a NumPy array")

        if not brand_colors:
            raise ValueError("At least one brand color is required")

        if k_clusters < 3 or k_clusters > 16:
            raise ValueError("k_clusters must be between 3 and 16")

        palette = self._build_palette(brand_colors)
        has_neutral_brand = any(c.is_neutral for c in palette)

        # 1) Preprocess image
        bgr = self._ensure_3_channel_bgr(bgr_image)
        bgr_resized = _resize_image_keep_aspect(bgr, self.max_image_side)
        lab_image = self._image_to_lab(bgr_resized)

        h, w = lab_image.shape[:2]
        total_pixels = int(h * w)

        # 2) K-means clustering in Lab space
        centers, labels, coverage = self._kmeans_clusters(lab_image, k_clusters)

        # 3) Compute distances from each cluster center to each brand color
        centers_expanded = centers[:, np.newaxis, :]  # (k,1,3)
        brand_labs = np.stack([c.lab for c in palette], axis=0)  # (B,3)
        brand_labs_expanded = brand_labs[np.newaxis, :, :]  # (1,B,3)

        # distances: (k, B)
        dists = np.linalg.norm(centers_expanded - brand_labs_expanded, axis=2)

        nearest_brand_indices = np.argmin(dists, axis=1)  # (k,)
        min_dists = dists[np.arange(dists.shape[0]), nearest_brand_indices]  # (k,)

        max_d = max(self.max_lab_distance, 1e-6)

        B = len(palette)
        raw_coverage_brand = np.zeros(B, dtype=np.float64)
        adjusted_coverage_brand = np.zeros(B, dtype=np.float64)
        distance_sums_brand = np.zeros(B, dtype=np.float64)
        distance_counts_brand = np.zeros(B, dtype=np.float64)

        overall_score = 0.0

        for i in range(k_clusters):
            cluster_center_lab = centers[i]
            cluster_cov = float(coverage[i])
            if cluster_cov <= 0:
                continue

            brand_idx = int(nearest_brand_indices[i])
            brand = palette[brand_idx]
            dist = float(min_dists[i])

            # closeness in [0,1]
            closeness = max(0.0, 1.0 - (dist / max_d))

            # neutral handling
            cluster_chroma = _chroma_from_lab(cluster_center_lab)
            cluster_is_neutral = cluster_chroma < NEUTRAL_CHROMA_THRESHOLD

            neutral_multiplier = 1.0
            if cluster_is_neutral and not has_neutral_brand:
                neutral_multiplier = NEUTRAL_PENALTY_WHEN_NO_NEUTRALS

            # contribution to global score
            # (no brand.weight anymore — all colors are equally important)
            cluster_score = cluster_cov * closeness * neutral_multiplier
            overall_score += cluster_score

            # brand-wise aggregations
            raw_coverage_brand[brand_idx] += cluster_cov
            adjusted_coverage_brand[brand_idx] += cluster_cov * closeness * neutral_multiplier
            distance_sums_brand[brand_idx] += dist
            distance_counts_brand[brand_idx] += 1.0

        # overall_score ∈ [0,1] (modulo neutral penalties), so map to 0–100
        alignment_score = float(round(overall_score * 100.0, 2))

        # per-brand breakdown
        brand_coverage_list = []
        for idx, brand in enumerate(palette):
            raw_cov_pct = float(round(raw_coverage_brand[idx] * 100.0, 2))
            adj_cov_pct = float(round(adjusted_coverage_brand[idx] * 100.0, 2))
            if distance_counts_brand[idx] > 0:
                avg_dist = float(distance_sums_brand[idx] / distance_counts_brand[idx])
            else:
                avg_dist = float("nan")

            brand_coverage_list.append(
                {
                    "hex": brand.hex,
                    "raw_coverage_percent": raw_cov_pct,
                    "adjusted_coverage_percent": adj_cov_pct,
                    "avg_distance": avg_dist,
                }
            )

        # Build top detected colors list (sorted by coverage, top 3)
        detected_colors_list = []
        for i in range(k_clusters):
            cluster_cov = float(coverage[i])
            if cluster_cov <= 0:
                continue

            cluster_center_lab = centers[i]
            brand_idx = int(nearest_brand_indices[i])
            brand = palette[brand_idx]
            dist = float(min_dists[i])

            # Convert cluster center back to hex
            cluster_hex = self._lab_to_hex(cluster_center_lab)

            # Match percentage (closeness)
            match_pct = max(0.0, (1.0 - (dist / max_d)) * 100.0)

            detected_colors_list.append(
                {
                    "detected_color": cluster_hex,
                    "nearest_brand_color": brand.hex,
                    "match_percentage": round(match_pct, 1),
                    "coverage_percentage": round(cluster_cov * 100.0, 1),
                    "distance": dist,
                }
            )

        # Sort by coverage (descending) and take top 3
        detected_colors_list.sort(key=lambda x: float(str(x["coverage_percentage"])), reverse=True)
        top_detected_colors = detected_colors_list[:3]

        result: dict[str, Any] = {
            "alignment_score": alignment_score,
            "total_pixels_analyzed": total_pixels,
            "brand_color_coverage": brand_coverage_list,
            "top_detected_colors": top_detected_colors,
            "debug": {
                "image_size": {"width": int(w), "height": int(h)},
                "k_clusters": k_clusters,
                "max_lab_distance": self.max_lab_distance,
                "has_neutral_brand": has_neutral_brand,
            },
        }

        # Generate heatmap if requested
        if generate_heatmap:
            heatmap_base64 = self._generate_heatmap(bgr_resized, labels, min_dists, h, w, max_d)
            result["heatmap_base64"] = heatmap_base64

        return result

    # ---------- internal helpers ----------

    def _build_palette(self, specs: list[BrandColorSpec]) -> list[_BrandColor]:
        palette: list[_BrandColor] = []
        for spec in specs:
            rgb = _hex_to_rgb(spec.hex)
            lab = _rgb_to_lab_opencv(rgb)
            chroma = _chroma_from_lab(lab)
            is_neutral = chroma < NEUTRAL_CHROMA_THRESHOLD
            palette.append(
                _BrandColor(
                    hex="#" + spec.hex.strip().lstrip("#").lower(),
                    lab=lab,
                    is_neutral=is_neutral,
                )
            )
        return palette

    def _ensure_3_channel_bgr(self, img: np.ndarray) -> np.ndarray:
        """Make sure the image is 3-channel BGR (no alpha, not grayscale)."""
        if img.ndim == 2:
            # grayscale -> BGR
            return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        if img.ndim == 3 and img.shape[2] == 4:
            # BGRA -> BGR (drop alpha; or composite over white/black if you prefer)
            return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        if img.ndim == 3 and img.shape[2] == 3:
            return img

        raise ValueError(f"Unsupported image shape: {img.shape}")

    def _image_to_lab(self, bgr: np.ndarray) -> np.ndarray:
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
        return lab.astype(np.float32)

    def _lab_to_hex(self, lab: np.ndarray) -> str:
        """Convert Lab array back to hex string."""
        lab_pixel = np.array([[lab]], dtype=np.float32).astype(np.uint8)
        bgr_pixel = cv2.cvtColor(lab_pixel, cv2.COLOR_LAB2BGR)
        b, g, r = int(bgr_pixel[0, 0, 0]), int(bgr_pixel[0, 0, 1]), int(bgr_pixel[0, 0, 2])
        return f"#{r:02x}{g:02x}{b:02x}"

    def _kmeans_clusters(
        self,
        lab_image: np.ndarray,
        k: int,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Run k-means in Lab space.

        Returns:
            centers: (k, 3) Lab cluster centers
            labels:  (H*W,) cluster index per pixel
            coverage: (k,) fraction of pixels in each cluster
        """
        h, w, _ = lab_image.shape
        pixels = lab_image.reshape((-1, 3)).astype(np.float32)

        criteria = (
            cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
            20,
            0.5,
        )
        attempts = 3

        _, labels, centers = cv2.kmeans(  # type: ignore[call-overload]
            data=pixels,
            K=k,
            bestLabels=None,
            criteria=criteria,
            attempts=attempts,
            flags=cv2.KMEANS_PP_CENTERS,
        )

        labels = labels.flatten()
        counts = np.bincount(labels, minlength=k).astype(np.float64)
        total = float(pixels.shape[0])
        coverage = counts / total

        return centers, labels, coverage

    def _generate_heatmap(
        self,
        bgr_image: np.ndarray,
        labels: np.ndarray,
        min_dists: np.ndarray,
        h: int,
        w: int,
        max_d: float,
    ) -> str:
        """
        Generate a heatmap overlay showing brand color alignment per pixel.

        Green = on-brand (close to brand colors)
        Yellow = somewhat close
        Red = off-brand (far from brand colors)

        Args:
            bgr_image: Original BGR image (resized)
            labels: Cluster label per pixel (H*W,)
            min_dists: Distance from each cluster to nearest brand color (k,)
            h: Image height
            w: Image width
            max_d: Maximum Lab distance threshold

        Returns:
            Base64-encoded PNG image string
        """
        # Map each pixel to its cluster's distance
        pixel_dists = min_dists[labels]  # (H*W,)
        pixel_dists = pixel_dists.reshape((h, w))

        # Normalize distances to [0, 1] where 0 = on-brand, 1 = off-brand
        normalized = np.clip(pixel_dists / max_d, 0.0, 1.0)

        # Create heatmap using OpenCV colormap
        # COLORMAP_JET: Blue (good) -> Green -> Yellow -> Red (bad)
        # We want Green (good) -> Yellow -> Red (bad), so we'll use a custom approach
        # Or use COLORMAP_RdYlGn reversed

        # Scale to 0-255 for colormap
        heatmap_gray = (normalized * 255).astype(np.uint8)

        # Apply colormap - COLORMAP_JET gives blue->green->yellow->red
        # We invert so low distance (good) = green, high distance (bad) = red
        heatmap_color = cv2.applyColorMap(heatmap_gray, cv2.COLORMAP_JET)

        # Swap red and blue channels to get green->yellow->red gradient
        # JET is: blue (0) -> cyan -> green -> yellow -> red (255)
        # We want: green (0) -> yellow -> red (255)
        # So we remap: multiply by 0.6 and offset to start from green region
        heatmap_gray_remapped = np.clip(heatmap_gray * 0.6 + 80, 0, 255).astype(np.uint8)
        heatmap_color = cv2.applyColorMap(heatmap_gray_remapped, cv2.COLORMAP_JET)

        # Blend with original image (50% opacity)
        blended = cv2.addWeighted(bgr_image, 0.5, heatmap_color, 0.5, 0)

        # Encode to PNG and then base64
        success, encoded = cv2.imencode(".png", blended)
        if not success:
            raise RuntimeError("Failed to encode heatmap image")

        base64_str = base64.b64encode(encoded.tobytes()).decode("utf-8")
        return f"data:image/png;base64,{base64_str}"
