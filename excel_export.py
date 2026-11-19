"""Excel-Export mit Konfidenz-Ampelformatierung."""
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from config import EXCEL_HEADERS

RED_FILL = PatternFill(start_color="FFC7CE", fill_type="solid")
YELLOW_FILL = PatternFill(start_color="FFEB9C", fill_type="solid")
GREEN_FILL = PatternFill(start_color="C6EFCE", fill_type="solid")
HEADER_FILL = PatternFill(start_color="4472C4", fill_type="solid")


def _fill_for(conf: int) -> PatternFill | None:
    if conf < 70:
        return RED_FILL
    if conf < 90:
        return YELLOW_FILL
    return GREEN_FILL


def export(rows: list[dict], out_path: str | Path) -> Path:
    """Schreibt die Ergebnis-Zeilen in eine .xlsx-Datei.

    Jede Zeile: name, datum, arbeitstage, urlaubstage, krankheitstage,
    confidence, geprueft, quelle (Dateiname).
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Zeiterfassung"

    ws.append(EXCEL_HEADERS + ["Quelldatei"])
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center")

    for r in rows:
        ws.append([
            r.get("name", ""),
            r.get("datum", ""),
            r.get("arbeitstage", 0),
            r.get("urlaubstage", 0),
            r.get("krankheitstage", 0),
            r.get("confidence", 0),
            r.get("geprueft", ""),
            r.get("quelle", ""),
        ])
        conf_cell = ws.cell(row=ws.max_row, column=6)
        fill = _fill_for(int(r.get("confidence", 0)))
        if fill:
            conf_cell.fill = fill

    for i, width in enumerate([24, 12, 13, 13, 15, 14, 16, 30], start=1):
        ws.column_dimensions[get_column_letter(i)].width = width
    ws.freeze_panes = "A2"

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = out.with_name(f"{out.stem}_{stamp}{out.suffix}")
    wb.save(out)
    return out


def export_secondary_sheet(rows: list[dict], out_path: str | Path) -> Path:
    """Fügt zur bestehenden Datei ein Statistikblatt hinzu."""
    wb = load_workbook(out_path)
    if "Statistik" in wb.sheetnames:
        del wb["Statistik"]
    ws = wb.create_sheet("Statistik")
    ws.append(["Metrik", "Wert"])
    ws.append(["Anzahl Seiten", len(rows)])
    if rows:
        confs = [int(r.get("confidence", 0)) for r in rows]
        ws.append(["Durchschnitt Konfidenz", round(sum(confs) / len(confs), 1)])
        ws.append(["Seiten unter 70 %", sum(1 for c in confs if c < 70)])
        ws.append(["Seiten ab 90 %", sum(1 for c in confs if c >= 90)])
    for cell in ws[1]:
        cell.font = Font(bold=True)
    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 14
    ws.freeze_panes = "A2"
    wb.save(out_path)
    return Path(out_path)
