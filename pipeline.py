"""Single shared batch pipeline used by GUI and CLI."""
import logging
from pathlib import Path
from config import DEFAULT_OUTPUT
from confidence import page_confidence
from preprocessing import image_quality_score
from schemas import FieldResult, PageEvaluation, PageResult
from validation import check_plausibility

log = logging.getLogger(__name__)
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def list_images(input_dir: str | Path) -> list[Path]:
    directory = Path(input_dir)
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.iterdir()
                  if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES)


def process_image(image_path: str | Path) -> PageEvaluation:
    path = Path(image_path)
    from ocr_engine import extract
    quality = image_quality_score(path)
    first, second = extract(path)
    plausible, issues = check_plausibility(first)
    score, breakdown = page_confidence(first, second, quality, plausible)
    if not plausible:
        score = min(score, 89)
    return PageEvaluation(source_file=path.name, result=first,
                          page_confidence=score, quality_breakdown=breakdown,
                          issues=issues)


def failed_evaluation(image_path: str | Path, exc: Exception) -> PageEvaluation:
    return PageEvaluation(
        source_file=Path(image_path).name,
        result=PageResult(name=FieldResult(), datum=FieldResult()),
        page_confidence=0, quality_breakdown={}, issues=["Verarbeitung fehlgeschlagen"],
        status="failed", error=f"{type(exc).__name__}: {exc}",
    )


def evaluation_to_row(evaluation: PageEvaluation) -> dict:
    result = evaluation.result
    return {
        "name": result.name.value,
        "datum": result.datum.value,
        "arbeitstage": result.arbeitstage,
        "urlaubstage": result.urlaubstage,
        "krankheitstage": result.krankheitstage,
        "confidence": evaluation.page_confidence,
        "geprueft": "Ja" if evaluation.human_reviewed else "",
        "status": evaluation.status,
        "quelle": evaluation.source_file,
        "fehler": evaluation.error or "; ".join(evaluation.issues),
    }


def process_batch(input_dir: str | Path) -> list[PageEvaluation]:
    images = list_images(input_dir)
    if not images:
        raise FileNotFoundError(f"Keine unterstützten Bilder in {input_dir} gefunden")
    evaluations = []
    for image in images:
        try:
            evaluation = process_image(image)
        except Exception as exc:
            log.exception("Verarbeitung von %s fehlgeschlagen", image.name)
            evaluation = failed_evaluation(image, exc)
        evaluations.append(evaluation)
        log.info("%s: %s (%d%%)", image.name, evaluation.status,
                 evaluation.page_confidence)
    return evaluations


def run_batch(input_dir: str | Path,
              out_xlsx: str | Path | None = None) -> tuple[list[PageEvaluation], Path]:
    evaluations = process_batch(input_dir)
    output = Path(out_xlsx) if out_xlsx else (
        DEFAULT_OUTPUT / f"zeiterfassung_{Path(input_dir).name or 'ergebnis'}.xlsx")
    output = output.with_suffix(".xlsx")
    from excel_export import export
    written = export([evaluation_to_row(item) for item in evaluations], output)
    return evaluations, written
