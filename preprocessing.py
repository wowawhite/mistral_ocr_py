"""Image loading, normalization and image-quality heuristics."""
from pathlib import Path
import cv2
import numpy as np
from config import MAX_SIDE_PX, SHARPNESS_MIN


def load_and_preprocess(image_path: str | Path) -> np.ndarray:
    path = Path(image_path)
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Bild konnte nicht gelesen werden: {path}")
    height, width = image.shape[:2]
    if min(height, width) < 1:
        raise ValueError(f"Ungültige Bildabmessungen: {path}")
    scale = min(1.0, MAX_SIDE_PX / max(height, width))
    if scale < 1.0:
        image = cv2.resize(image, (max(1, int(width * scale)),
                                   max(1, int(height * scale))),
                           interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)


def image_quality_score(image_path: str | Path) -> float:
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None or image.size == 0:
        raise ValueError(f"Bild konnte nicht gelesen werden: {image_path}")
    sharpness = min(cv2.Laplacian(image, cv2.CV_64F).var() / SHARPNESS_MIN, 1.0)
    contrast = min(float(image.std()) / 60.0, 1.0)
    brightness = float(image.mean()) / 255.0
    brightness_score = max(0.0, 1.0 - abs(brightness - 0.5) * 2)
    return round(0.5 * sharpness + 0.3 * contrast + 0.2 * brightness_score, 3)
