"""Heuristic quality score (not a calibrated probability)."""
from config import W_CONSISTENCY, W_IMAGE_QUALITY, W_MODEL_SELF, W_PLAUSIBILITY
from schemas import PageResult


def _consistency_percent(first: PageResult, second: PageResult) -> float:
    pairs = [
        (first.name.value.strip().casefold(), second.name.value.strip().casefold()),
        (first.datum.value.strip(), second.datum.value.strip()),
        (first.arbeitstage, second.arbeitstage),
        (first.urlaubstage, second.urlaubstage),
        (first.krankheitstage, second.krankheitstage),
    ]
    return sum(100 for a, b in pairs if a == b) / len(pairs)


def page_confidence(first: PageResult, second: PageResult,
                    image_quality: float, plausibility_ok: bool) -> tuple[int, dict]:
    field_scores = [first.name.confidence, first.datum.confidence,
                    first.arbeitstage_conf, first.urlaubstage_conf,
                    first.krankheitstage_conf]
    model_self = sum(field_scores) / len(field_scores)
    consistency = _consistency_percent(first, second)
    plausibility = 100.0 if plausibility_ok else 0.0
    quality = max(0.0, min(float(image_quality or 0.0), 1.0)) * 100
    breakdown = {
        "modell_selbsteinschaetzung": round(model_self, 1),
        "konsistenz_zweitdurchlauf": round(consistency, 1),
        "plausibilitaet": plausibility,
        "bildqualitaet": round(quality, 1),
    }
    total = (W_MODEL_SELF * model_self + W_CONSISTENCY * consistency
             + W_PLAUSIBILITY * plausibility + W_IMAGE_QUALITY * quality)
    return round(max(0, min(total, 100))), breakdown
