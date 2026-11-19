"""Kommandozeilen-Batchverarbeitung (ohne GUI)."""
import argparse
import logging
from pathlib import Path

from config import DEFAULT_OUTPUT, MODEL
from excel_export import export
from pipeline import evaluation_to_row, list_images, process_image


def main() -> int:
    parser = argparse.ArgumentParser(
        description="OCR-Erfassung handgeschriebener Zeitzettel "
                    f"({MODEL}, lokal via Ollama).")
    parser.add_argument("input", type=Path,
                        help="Ordner mit Fotos der Zeitzettel")
    parser.add_argument("-o", "--output", type=Path,
                        default=DEFAULT_OUTPUT / "zeiterfassung.xlsx",
                        help="Pfad der Ausgabedatei (.xlsx)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s")

    images = list_images(args.input)
    if not images:
        print(f"FEHLER: Keine Bilder in {args.input} gefunden.")
        return 1

    print(f"{len(images)} Bilder in {args.input}\n")
    rows = []
    for i, img in enumerate(images, 1):
        print(f"[{i}/{len(images)}] {img.name} ...", flush=True)
        try:
            ev = process_image(img)
        except Exception as exc:
            print(f"    FEHLER: {exc}")
            continue
        print(f"    Konfidenz: {ev.page_confidence} % ({ev.verdict})")
        if ev.issues:
            for issue in ev.issues:
                print(f"    Hinweis: {issue}")
        rows.append(evaluation_to_row(ev))

    if not rows:
        print("Keine Seite erfolgreich verarbeitet.")
        return 2

    written = export(rows, args.output)
    print(f"\nFertig. {len(rows)} Seiten geschrieben nach: {written}")
    return 0
