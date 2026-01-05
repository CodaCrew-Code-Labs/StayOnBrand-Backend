from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np
import pytesseract
from pytesseract import Output

# ==========================
# Data structures
# ==========================


@dataclass
class TextRegion:
    text: str
    bbox: tuple[int, int, int, int]  # x, y, w, h
    confidence: float
    contrast: float = 0.0
    is_large: bool = False
    clutter: float = 0.0
    cb_min_contrast: float = 0.0  # min contrast across simulated color-blind variants


# ==========================
# WCAG utilities
# ==========================


def _srgb_to_linear(c: float) -> float:
    c = c / 255.0
    if c <= 0.03928:
        return c / 12.92
    return float(((c + 0.055) / 1.055) ** 2.4)


def relative_luminance(rgb: np.ndarray) -> float:
    """
    rgb: np.array([R, G, B]) in 0-255
    """
    r, g, b = [_srgb_to_linear(float(v)) for v in rgb]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(c1: np.ndarray, c2: np.ndarray) -> float:
    """
    c1, c2: np.array([R, G, B]) in 0-255
    """
    L1 = relative_luminance(c1)
    L2 = relative_luminance(c2)
    light = max(L1, L2)
    dark = min(L1, L2)
    return (light + 0.05) / (dark + 0.05)


# ==========================
# Color-blindness simulation
# ==========================


def simulate_protanopia(image: np.ndarray) -> np.ndarray:
    """
    Simple protanopia simulation (not medically perfect, but good enough for heuristic scoring).
    """
    # Matrix from Brettel et al.–style approximations (rough)
    M = np.array([[0.56667, 0.43333, 0.0], [0.55833, 0.44167, 0.0], [0.0, 0.24167, 0.75833]])
    img = image.astype(np.float32) / 255.0
    transformed = img @ M.T
    transformed = np.clip(transformed, 0, 1)
    result: np.ndarray = (transformed * 255).astype(np.uint8)
    return result


def simulate_deuteranopia(image: np.ndarray) -> np.ndarray:
    """
    Simple deuteranopia simulation.
    """
    M = np.array([[0.625, 0.375, 0.0], [0.7, 0.3, 0.0], [0.0, 0.3, 0.7]])
    img = image.astype(np.float32) / 255.0
    transformed = img @ M.T
    transformed = np.clip(transformed, 0, 1)
    result: np.ndarray = (transformed * 255).astype(np.uint8)
    return result


# ==========================
# Image pre-processing
# ==========================


def load_and_resize(image_path: str, max_dim: int = 1024) -> np.ndarray:
    """
    Load image with OpenCV (BGR) and resize preserving aspect ratio.
    No cropping.
    """
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")

    h, w = img.shape[:2]
    scale = max_dim / max(h, w) if max(h, w) > max_dim else 1.0
    if scale < 1.0:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return img


def load_from_bytes(image_bytes: bytes, max_dim: int = 1024) -> np.ndarray:
    """
    Load image from bytes and resize preserving aspect ratio.
    No cropping.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image from bytes")

    h, w = img.shape[:2]
    scale = max_dim / max(h, w) if max(h, w) > max_dim else 1.0
    if scale < 1.0:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return img


# ==========================
# Text detection via Tesseract
# ==========================


def detect_text_regions(image: np.ndarray, conf_threshold: int = 60) -> list[TextRegion]:
    """
    Use Tesseract to detect text bounding boxes.
    Returns a list of TextRegion objects.
    """
    # Convert BGR -> RGB for Tesseract
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    data = pytesseract.image_to_data(rgb, output_type=Output.DICT)

    regions: list[TextRegion] = []
    n_boxes = len(data["text"])
    for i in range(n_boxes):
        text = data["text"][i].strip()
        conf = int(float(data["conf"][i]))
        if not text or conf < conf_threshold:
            continue

        x, y, w, h = (data["left"][i], data["top"][i], data["width"][i], data["height"][i])

        regions.append(TextRegion(text=text, bbox=(x, y, w, h), confidence=conf))
    return regions


# ==========================
# Foreground / Background color estimation
# ==========================


def sample_region_colors(
    image: np.ndarray, bbox: tuple[int, int, int, int]
) -> tuple[np.ndarray, np.ndarray]:
    """
    Heuristic: foreground = center area, background = border ring around the text box.
    Returns (fg_color_rgb, bg_color_rgb).
    """
    h_img, w_img = image.shape[:2]
    x, y, w, h = bbox

    # Clamp bbox to image bounds
    x = max(0, x)
    y = max(0, y)
    w = max(1, min(w, w_img - x))
    h = max(1, min(h, h_img - y))

    roi = image[y : y + h, x : x + w]  # BGR
    if roi.size == 0:
        # fallback: whole image
        roi = image

    # foreground: center 50% box
    cx1 = int(w * 0.25)
    cy1 = int(h * 0.25)
    cx2 = int(w * 0.75)
    cy2 = int(h * 0.75)
    fg_roi = roi[cy1:cy2, cx1:cx2] if cy2 > cy1 and cx2 > cx1 else roi

    # background: border ring (outer minus inner)
    # Create 2D mask for height x width only
    roi_h, roi_w = roi.shape[:2]
    border = np.zeros((roi_h, roi_w), dtype=bool)
    border[0 : int(roi_h * 0.15), :] = True
    border[int(roi_h * 0.85) :, :] = True
    border[:, 0 : int(roi_w * 0.15)] = True
    border[:, int(roi_w * 0.85) :] = True
    bg_pixels = roi[border]  # This now correctly gives (N, 3) array

    if bg_pixels.size < 10 or len(bg_pixels.shape) != 2:
        bg_pixels = roi.reshape(-1, 3)

    fg_pixels = fg_roi.reshape(-1, 3)

    # convert BGR -> RGB
    fg_rgb = fg_pixels[:, ::-1]
    bg_rgb = bg_pixels[:, ::-1]

    fg_color = fg_rgb.mean(axis=0)
    bg_color = bg_rgb.mean(axis=0)

    return fg_color, bg_color


# ==========================
# Clutter / Legibility
# ==========================


def compute_clutter_score(image: np.ndarray, bbox: tuple[int, int, int, int]) -> float:
    """
    Estimate clutter (0-1). Higher means more clutter (worse).
    Uses edge density inside the text bounding box.
    """
    x, y, w, h = bbox
    h_img, w_img = image.shape[:2]
    x = max(0, x)
    y = max(0, y)
    w = max(1, min(w, w_img - x))
    h = max(1, min(h, h_img - y))

    roi = image[y : y + h, x : x + w]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # Canny edge detection
    edges = cv2.Canny(gray, 100, 200)
    edge_density = edges.mean() / 255.0  # 0-1

    # Normalize: use simple clamp. Above 0.3 is considered very cluttered.
    clutter = min(edge_density / 0.3, 1.0)
    return float(clutter)


# ==========================
# Large-text heuristic
# ==========================


def is_large_text(bbox: tuple[int, int, int, int], dpi: int = 96) -> bool:
    """
    Heuristic: anything with height >= 24px (approx 18pt at 96 dpi) is 'large text'.
    """
    _, _, _, h = bbox
    # At 96 DPI: 1pt =~ 96/72 px. 18pt ~ 24px.
    return h >= 24


# ==========================
# Per-region metrics
# ==========================


def enrich_text_regions_with_metrics(
    image: np.ndarray, regions: list[TextRegion]
) -> list[TextRegion]:
    """
    Compute contrast, large-text flag, clutter, and color-blind contrast for each region.
    """
    # Precompute color-blind simulated images
    prot = simulate_protanopia(image)
    deut = simulate_deuteranopia(image)

    for r in regions:
        fg, bg = sample_region_colors(image, r.bbox)
        c = contrast_ratio(fg, bg)

        # Contrast under color-blind variants
        # Sample the same region from simulated images
        x, y, w, h = r.bbox
        fg_p, bg_p = sample_region_colors(prot, r.bbox)
        fg_d, bg_d = sample_region_colors(deut, r.bbox)
        c_p = contrast_ratio(fg_p, bg_p)
        c_d = contrast_ratio(fg_d, bg_d)

        r.contrast = float(c)
        r.is_large = is_large_text(r.bbox)
        r.clutter = compute_clutter_score(image, r.bbox)
        r.cb_min_contrast = float(min(c_p, c_d))

    return regions


# ==========================
# Metric aggregation
# ==========================


def compute_text_contrast_score(regions: list[TextRegion]) -> float:
    """
    Return 0-1 score based on WCAG-like thresholds:
      - 4.5:1 for normal text
      - 3.0:1 for large text
    """
    if not regions:
        return 1.0  # nothing to score, assume OK

    passes = 0
    total = 0
    for r in regions:
        threshold = 3.0 if r.is_large else 4.5
        if r.contrast >= threshold:
            passes += 1
        total += 1

    return passes / total if total > 0 else 1.0


def compute_large_text_usage_score(regions: list[TextRegion]) -> float:
    """
    Score 0-1: higher if more text is large (assuming large text is more accessible).
    Full score if >=60% of text is 'large'.
    """
    if not regions:
        return 1.0

    total = len(regions)
    large_count = sum(1 for r in regions if r.is_large)
    frac_large = large_count / total

    # Linear scale: 0 at 0%, 1 at 60%+
    return min(frac_large / 0.6, 1.0)


def compute_legibility_score(regions: list[TextRegion]) -> float:
    """
    Legibility = 1 - average clutter.
    Clutter is clamped 0-1; 0 clean, 1 very cluttered.
    """
    if not regions:
        return 1.0

    avg_clutter = sum(r.clutter for r in regions) / len(regions)
    return max(0.0, 1.0 - avg_clutter)


def compute_colorblind_safety_score(regions: list[TextRegion]) -> float:
    """
    For each region, ensure contrast remains above WCAG threshold in color-blind simulations.
    If contrast drops below threshold, penalise.

    Score = average of per-region safety scores.
    """
    if not regions:
        return 1.0

    scores = []
    for r in regions:
        threshold = 3.0 if r.is_large else 4.5
        if r.cb_min_contrast >= threshold:
            scores.append(1.0)
        else:
            # scale 0-1 depending on how close it is to threshold
            # 0 at 0 contrast, 1 at threshold or above
            s = max(0.0, min(r.cb_min_contrast / threshold, 1.0))
            scores.append(s)

    return sum(scores) / len(scores)


def aggregate_overall_score(
    text_contrast_score: float,
    large_text_score: float,
    legibility_score: float,
    colorblind_score: float,
) -> float:
    """
    Weighted aggregate -> 0-1.
    Adjust weights as you see fit.
    """
    return (
        0.5 * text_contrast_score
        + 0.15 * large_text_score
        + 0.2 * legibility_score
        + 0.15 * colorblind_score
    )


# ==========================
# Main entrypoint
# ==========================


def evaluate_image_accessibility(image_path: str) -> dict[str, Any]:
    """
    High-level function: given an image path,
    returns a JSON-serializable dict with:
      - overall_score (0-100)
      - individual metric scores (0-100)
      - per-region diagnostics
    """
    image = load_and_resize(image_path)
    return _evaluate_image(image)


def evaluate_image_accessibility_from_bytes(image_bytes: bytes) -> dict[str, Any]:
    """
    High-level function: given image bytes,
    returns a JSON-serializable dict with:
      - overall_score (0-100)
      - individual metric scores (0-100)
      - per-region diagnostics
    """
    image = load_from_bytes(image_bytes)
    return _evaluate_image(image)


def _evaluate_image(image: np.ndarray) -> dict[str, Any]:
    """
    Internal function that evaluates an already-loaded image.
    """
    regions = detect_text_regions(image)
    regions = enrich_text_regions_with_metrics(image, regions)

    text_contrast = compute_text_contrast_score(regions)
    large_text = compute_large_text_usage_score(regions)
    legibility = compute_legibility_score(regions)
    colorblind = compute_colorblind_safety_score(regions)
    overall = aggregate_overall_score(text_contrast, large_text, legibility, colorblind)

    result = {
        "overall_score": round(overall * 100, 2),
        "metrics": {
            "text_contrast_score": round(text_contrast * 100, 2),
            "large_text_score": round(large_text * 100, 2),
            "legibility_score": round(legibility * 100, 2),
            "colorblind_safety_score": round(colorblind * 100, 2),
        },
        "regions": [
            {
                "text": r.text,
                "bbox": {
                    "x": r.bbox[0],
                    "y": r.bbox[1],
                    "w": r.bbox[2],
                    "h": r.bbox[3],
                },
                "confidence": r.confidence,
                "contrast": round(r.contrast, 2),
                "is_large": r.is_large,
                "clutter": round(r.clutter, 3),
                "colorblind_min_contrast": round(r.cb_min_contrast, 2),
            }
            for r in regions
        ],
        "notes": [
            "This score only reflects image-level accessibility (contrast, text size, clutter, color-blind safety).",
            "It does NOT validate full WCAG compliance (no alt text, semantics, keyboard, or structure checks).",
        ],
    }
    return result
