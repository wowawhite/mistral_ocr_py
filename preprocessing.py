"""Bildvorverarbeitung und Bildqualitätsbewertung (OpenCV)."""
from pathlib import Path

import cv2
import numpy as np

from config import MAX_SIDE_PX, SHARPNESS_MIN


def load_and_preprocess(image_path: str | Path) -> np.ndarray:
    """Lädt ein Foto, skaliert es auf eine verarbeitbare Größe und
    verbessert Kontrast. Rückgabe: verarbeitetes BGR-Bild."""
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Bild konnte nicht gelesen werden: {image_path}")

    h, w = img.shape[:2]
    scale = MAX_SIDE_PX / max(h, w)
    if scale < 1.0:
        img = cv2.resize(img, (int(w * scale), int(h * scale)),
                         interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)


def image_quality_score(image_path: str | Path) -> float:
    """Bildqualität als Wert 0.0-1.0 aus Schärfe und Kontrast."""
    img = cv2.imread(str(image_path))
    if img is None:
        return 0.0
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    sharpness = min(laplacian_var / SHARPNESS_MIN, 1.0)

    contrast = min(gray.std() / 60.0, 1.0)

    brightness = gray.mean() / 255.0
    brightness_score = 1.0 - abs(brightness - 0.5) * 2

    return round(0.5 * sharpness + 0.3 * contrast
                 + 0.2 * max(brightness_score, 0.0), 3)
