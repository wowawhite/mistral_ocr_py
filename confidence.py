"""Berechnung der Seiten-Konfidenz (0-100 %) aus vier Signalen."""
from config import (W_CONSISTENCY, W_IMAGE_QUALITY, W_MODEL_SELF,
                    W_PLAUSIBILITY)
from schemas import PageResult


def _consistency_percent(r1: PageResult, r2: PageResult) -> float:
    pairs = [
        (r1.name.value.strip().lower(), r2.name.value.strip().lower()),
        (r1.datum.value.strip(), r2.datum.value.strip()),
        (r1.arbeitstage, r2.arbeitstage),
        (r1.urlaubstage, r2.urlaubstage),
        (r1.krankheitstage, r2.krankheitstage),
    ]
    matches = sum(100 for a, b in pairs if a == b)
    return matches / len(pairs)


def page_confidence(r1: PageResult, r2: PageResult,
                    image_quality: float,
                    plausibility_ok: bool) -> tuple[int, dict]:
    """Seiten-Konfidenz 0-100 und Aufschlüsselung der Anteile.

    image_quality: 0.0-1.0 aus preprocessing.image_quality_score().
    """
    field_scores = [
        r1.name.confidence,
        r1.datum.confidence,
        r1.arbeitstage_conf,
        r1.urlaubstage_conf,
        r1.krankheitstage_conf,
    ]
    model_self = sum(field_scores) / len(field_scores)
    consistency = _consistency_percent(r1, r2)
    plausibility = 100.0 if plausibility_ok else 0.0

    breakdown = {
        "modell_selbsteinschaetzung": round(model_self, 1),
        "konsistenz_zweitdurchlauf": round(consistency, 1),
        "plausibilitaet": round(plausibility, 1),
        "bildqualitaet": round((image_quality or 0.0) * 100, 1),
    }
    total = (W_MODEL_SELF * model_self
             + W_CONSISTENCY * consistency
             + W_PLAUSIBILITY * plausibility
             + W_IMAGE_QUALITY * (image_quality or 0.0) * 100)
    return round(max(0, min(total, 100))), breakdown
