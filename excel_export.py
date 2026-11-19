"""Safe Excel export with status, quality score and statistics."""
from datetime import datetime
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from config import EXCEL_HEADERS

RED_FILL = PatternFill(start_color="FFC7CE", fill_type="solid")
YELLOW_FILL = PatternFill(start_color="FFEB9C", fill_type="solid")
GREEN_FILL = PatternFill(start_color="C6EFCE", fill_type="solid")
HEADER_FILL = PatternFill(start_color="4472C4", fill_type="solid")


def safe_excel_value(value):
    """Force untrusted OCR strings to text, never formulas."""
    if not isinstance(value, str):
        return value
    if value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def _score_fill(score: int):
    if score < 70:
        return RED_FILL
    if score < 90:
        return YELLOW_FILL
    return GREEN_FILL


def export(rows: list[dict], out_path: str | Path) -> Path:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Zeiterfassung"
    sheet.append(EXCEL_HEADERS)
    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center")
    for row in rows:
        values = [
            safe_excel_value(row.get("name", "")),
            safe_excel_value(row.get("datum", "")),
            row.get("arbeitstage", 0), row.get("urlaubstage", 0),
            row.get("krankheitstage", 0), row.get("confidence", 0),
            row.get("geprueft", ""), row.get("status", "processed"),
            safe_excel_value(row.get("quelle", "")),
            safe_excel_value(row.get("fehler", "")),
        ]
        sheet.append(values)
        sheet.cell(sheet.max_row, 6).fill = _score_fill(int(row.get("confidence", 0)))
    widths = [24, 14, 13, 13, 15, 18, 18, 15, 30, 55]
    for index, width in enumerate(widths, 1):
        sheet.column_dimensions[get_column_letter(index)].width = width
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions

    stats = workbook.create_sheet("Statistik")
    stats.append(["Metrik", "Wert"])
    for cell in stats[1]:
        cell.font = Font(bold=True)
    scores = [int(row.get("confidence", 0)) for row in rows]
    stats.append(["Anzahl Eingabedokumente", len(rows)])
    stats.append(["Erfolgreich verarbeitet", sum(r.get("status") == "processed" for r in rows)])
    stats.append(["Fehlgeschlagen", sum(r.get("status") != "processed" for r in rows)])
    stats.append(["Menschlich geprüft", sum(bool(r.get("geprueft")) for r in rows)])
    stats.append(["Durchschnittlicher Qualitätswert", round(sum(scores) / len(scores), 1) if scores else 0])
    stats.column_dimensions["A"].width = 36
    stats.column_dimensions["B"].width = 18
    stats.freeze_panes = "A2"

    output = Path(out_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        output = output.with_name(f"{output.stem}_{stamp}{output.suffix}")
    workbook.save(output)
    return output
