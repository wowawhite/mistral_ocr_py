"""Pipeline-Orchestrierung: Bild -> Erkennung -> Konfidenz -> Zeile."""
import logging
import shutil
from pathlib import Path

from config import ARCHIVE_DIR_NAME, DEFAULT_OUTPUT, THRESHOLD_YELLOW
from confidence import page_confidence
from ocr_engine import extract
from preprocessing import image_quality_score
from schemas import PageEvaluation
from validation import check_plausibility

log = logging.getLogger(__name__)

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def list_images(input_dir: str | Path) -> list[Path]:
    d = Path(input_dir)
    if not d.is_dir():
        return []
    return sorted(p for p in d.iterdir()
                  if p.suffix.lower() in IMAGE_SUFFIXES and p.is_file())


def process_image(image_path: str | Path) -> PageEvaluation:
    """Verarbeitet ein Foto komplett und liefert das bewertete Ergebnis."""
    image_path = Path(image_path)
    quality = image_quality_score(image_path)
    r1, r2 = extract(image_path)
    ok, issues = check_plausibility(r1)
    conf, breakdown = page_confidence(r1, r2, quality, ok)
    return PageEvaluation(
        source_file=image_path.name,
        result=r1,
        page_confidence=conf,
        quality_breakdown=breakdown,
        issues=issues,
    )


def evaluation_to_row(ev: PageEvaluation) -> dict:
    r = ev.result
    return {
        "name": r.name.value,
        "datum": r.datum.value,
        "arbeitstage": r.arbeitstage,
        "urlaubstage": r.urlaubstage,
        "krankheitstage": r.krankheitstage,
        "confidence": ev.page_confidence,
        "geprueft": "Ja" if ev.verdict == "GRUEN" else "",
        "quelle": ev.source_file,
    }


def run_batch(input_dir: str | Path,
              out_xlsx: str | Path | None = None) -> tuple[list[PageEvaluation], Path]:
    """Verarbeitet alle Bilder eines Ordners und exportiert die Excel.

    Rückgabe: (alle Auswertungen, Pfad der Excel-Datei).
    """
    input_dir = Path(input_dir)
    images = list_images(input_dir)
    if not images:
        raise FileNotFoundError(
            f"Keine Bilder in {input_dir} gefunden "
            f"(unterstützt: {', '.join(sorted(IMAGE_SUFFIXES))})")

    out_path = Path(out_xlsx) if out_xlsx else (
        DEFAULT_OUTPUT / (f"zeiterfassung_"
                          f"{input_dir.name or 'ergebnis'}.xlsx"))
    out_path = out_path.with_suffix(".xlsx")

    evaluations: list[PageEvaluation] = []
    rows: list[dict] = []
    for img in images:
        try:
            ev = process_image(img)
        except Exception as exc:
            log.error("Fehler bei %s: %s", img.name, exc)
            ev = PageEvaluation(
                source_file=img.name,
                result=_error_result(),
                page_confidence=0,
                quality_breakdown={},
                issues=[f"Verarbeitungsfehler: {exc}"],
            )
        evaluations.append(ev)
        rows.append(evaluation_to_row(ev))
        log.info("%s -> %d %% (%s)", ev.source_file,
                 ev.page_confidence, ev.verdict)

    written = _write_excel(rows, out_path)
    _archive_low_confidence(input_dir, evaluations)
    return evaluations, written


def _error_result():
    from schemas import FieldResult, PageResult
    return PageResult(
        name=FieldResult(value="", confidence=0),
        datum=FieldResult(value="", confidence=0),
    )


def _write_excel(rows, out_path: Path) -> Path:
    from excel_export import export, export_secondary_sheet
    written = export(rows, out_path)
    export_secondary_sheet(rows, written)
    return written


def _archive_low_confidence(input_dir: Path, evs: list[PageEvaluation]):
    """Verschiebt Seiten unter dem Gelb-Schwellenwert in einen
    Wiederholungslauf-Ordner (Nachschärfen der Fotos empfohlen)."""
    archive = input_dir / ARCHIVE_DIR_NAME
    archive.mkdir(exist_ok=True)
    for ev in evs:
        if ev.verdict == "ROT":
            src = input_dir / ev.source_file
            if src.exists():
                shutil.move(str(src), archive / ev.source_file)
                log.info("Nachprüfen: %s verschoben nach %s",
                         ev.source_file, archive)
