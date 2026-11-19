"""Command-line batch processing; shares the same service as the GUI."""
import argparse
import logging
from pathlib import Path
from config import DEFAULT_OUTPUT, MODEL
from pipeline import run_batch


def main() -> int:
    parser = argparse.ArgumentParser(
        description=f"Lokale OCR-Zeiterfassung ({MODEL}, via Ollama)")
    parser.add_argument("input", type=Path, help="Ordner mit Zeitzettel-Fotos")
    parser.add_argument("-o", "--output", type=Path,
                        default=DEFAULT_OUTPUT / "zeiterfassung.xlsx")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        evaluations, written = run_batch(args.input, args.output)
    except FileNotFoundError as exc:
        parser.error(str(exc))
    failed = sum(item.status != "processed" for item in evaluations)
    print(f"\nFertig: {len(evaluations) - failed} erfolgreich, {failed} fehlgeschlagen.")
    print(f"Excel: {written}")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
