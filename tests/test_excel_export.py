from openpyxl import load_workbook
from excel_export import export, safe_excel_value


def test_formula_like_text_is_escaped():
    assert safe_excel_value("=1+1").startswith("'")


def test_export_includes_failed_rows_and_statistics(tmp_path):
    output = export([{
        "name": "=1+1", "datum": "", "arbeitstage": 0,
        "urlaubstage": 0, "krankheitstage": 0, "confidence": 0,
        "geprueft": "", "status": "failed", "quelle": "bad.jpg",
        "fehler": "unreadable",
    }], tmp_path / "out.xlsx")
    workbook = load_workbook(output, data_only=False)
    assert workbook.sheetnames == ["Zeiterfassung", "Statistik"]
    assert workbook["Zeiterfassung"]["A2"].data_type == "s"
    assert workbook["Zeiterfassung"]["A2"].value.startswith("'")
    assert workbook["Statistik"]["B4"].value == 1
