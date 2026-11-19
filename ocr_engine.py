"""Two-pass local OCR using Ollama with bounded retry handling."""
import base64
import logging
import time
from pathlib import Path

import cv2
import ollama

from config import (MODEL, NUM_CTX, OCR_RETRIES, OLLAMA_HOST,
                    OLLAMA_TIMEOUT, SYSTEM_PROMPT, TEMP_RUN1, TEMP_RUN2)
from preprocessing import load_and_preprocess
from schemas import PageResult

log = logging.getLogger(__name__)
_client = ollama.Client(host=OLLAMA_HOST, timeout=OLLAMA_TIMEOUT)


def _encode_image(image_path: str | Path) -> str:
    ok, buffer = cv2.imencode(".jpg", load_and_preprocess(image_path))
    if not ok:
        raise ValueError(f"Bild konnte nicht kodiert werden: {image_path}")
    return base64.b64encode(buffer.tobytes()).decode("ascii")


def _run_once(image_path: str | Path, temperature: float) -> PageResult:
    encoded = _encode_image(image_path)
    last_error = None
    for attempt in range(OCR_RETRIES + 1):
        try:
            response = _client.chat(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": "Analysiere diesen Zeitzettel.",
                     "images": [encoded]},
                ],
                options={"temperature": temperature, "num_ctx": NUM_CTX},
                think=False, format="json",
            )
            content = response.message.content.strip()
            return PageResult.model_validate_json(content)
        except Exception as exc:
            last_error = exc
            if attempt < OCR_RETRIES:
                time.sleep(min(2 ** attempt, 4))
    raise RuntimeError(f"OCR-Aufruf fehlgeschlagen: {last_error}") from last_error


def _mismatch_copy(result: PageResult) -> PageResult:
    data = result.model_dump()
    data["name"] = {"value": "__SECOND_PASS_FAILED__", "confidence": 0}
    data["datum"] = {"value": "__SECOND_PASS_FAILED__", "confidence": 0}
    data["arbeitstage"] = (result.arbeitstage + 1) % 32
    data["urlaubstage"] = (result.urlaubstage + 1) % 32
    data["krankheitstage"] = (result.krankheitstage + 1) % 32
    return PageResult.model_validate(data)


def extract(image_path: str | Path) -> tuple[PageResult, PageResult]:
    first = _run_once(image_path, TEMP_RUN1)
    log.info("OCR pass 1 completed: %s", Path(image_path).name)
    try:
        second = _run_once(image_path, TEMP_RUN2)
    except Exception:
        log.exception("OCR comparison pass failed: %s", Path(image_path).name)
        second = _mismatch_copy(first)
    return first, second
