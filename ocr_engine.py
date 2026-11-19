"""Erkennungs-Engine: Zwei Aufrufe von Qwen3-VL-8B via lokalem Ollama."""
import base64
import logging
from pathlib import Path

import ollama

from config import (MODEL, NUM_CTX, OLLAMA_HOST, SYSTEM_PROMPT,
                    TEMP_RUN1, TEMP_RUN2)
from preprocessing import load_and_preprocess
from schemas import PageResult

log = logging.getLogger(__name__)

_client = ollama.Client(host=OLLAMA_HOST)


def _encode_image(image_path: str | Path) -> str:
    """Verarbeitetes Bild (skaliert, Kontrast verbessert) als Base64."""
    import cv2
    path = Path(image_path)
    ok, buf = cv2.imencode(".jpg", load_and_preprocess(path))
    if not ok:
        raise ValueError(f"Bild konnte nicht kodiert werden: {path}")
    return base64.b64encode(buf.tobytes()).decode("ascii")


def _run_once(image_path: str | Path, temperature: float) -> PageResult:
    response = _client.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",
             "content": "Analysiere dieses Foto eines Zeitzettels.",
             "images": [_encode_image(image_path)]},
        ],
        options={"temperature": temperature, "num_ctx": NUM_CTX},
        think=False,
        format="json",
    )
    raw = response.message.content.strip()
    return PageResult.model_validate_json(raw)


def _mismatch_copy(r: PageResult) -> PageResult:
    """Kopie, die in keinem Feld mit r übereinstimmt – falls der
    Zweitdurchlauf technisch fehlschlägt (Konsistenz = 0)."""
    data = r.model_dump()
    data["name"] = {"value": "___NO_MATCH___", "confidence": 0}
    data["datum"] = {"value": "__.__.____", "confidence": 0}
    data["arbeitstage"] = data.get("arbeitstage", 0) + 1
    data["urlaubstage"] = data.get("urlaubstage", 0) + 1
    data["krankheitstage"] = data.get("krankheitstage", 0) + 1
    return PageResult.model_validate(data)


def extract(image_path: str | Path) -> tuple[PageResult, PageResult]:
    """Zwei Durchläufe mit variiertem Sampling. Rückgabe:
    (Hauptergebnis, Vergleichsergebnis für Konsistenzprüfung)."""
    r1 = _run_once(image_path, TEMP_RUN1)
    log.info("Durchlauf 1 ok: %s", Path(image_path).name)
    try:
        r2 = _run_once(image_path, TEMP_RUN2)
        log.info("Durchlauf 2 ok: %s", Path(image_path).name)
    except Exception as exc:
        log.warning("Durchlauf 2 fehlgeschlagen (%s) – "
                    "Konsistenz der Felder wird als 0 gewertet.", exc)
        r2 = _mismatch_copy(r1)
    return r1, r2
