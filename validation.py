"""Plausibilitätsprüfung der erkannten Merkmale."""
import re
from datetime import date

from schemas import PageResult

DATE_RE = re.compile(r"^\s*(\d{1,2})\.(\d{1,2})\.(\d{4})\s*$")


def parse_datum(value: str) -> date | None:
    m = DATE_RE.match(value or "")
    if not m:
        return None
    d, mo, y = (int(g) for g in m.groups())
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def check_plausibility(r: PageResult) -> tuple[bool, list[str]]:
    """Prüft fachliche Regeln. Rückgabe: (gültig?, Liste der Mängel)."""
    issues: list[str] = []

    if not r.name.value.strip():
        issues.append("Name ist leer")
    if r.name.confidence == 0:
        issues.append("Name nicht lesbar erkannt")

    parsed = parse_datum(r.datum.value)
    if parsed is None:
        issues.append(f"Datum nicht parsebar: '{r.datum.value}'")
        month_days = 31
    else:
        if parsed > date.today():
            issues.append(f"Datum liegt in der Zukunft: {parsed}")
        if parsed.year < 2000:
            issues.append(f"Datum unplausible Jahreszahl: {parsed}")
        import calendar
        month_days = calendar.monthrange(parsed.year, parsed.month)[1]

    total = r.arbeitstage + r.urlaubstage + r.krankheitstage
    if total > month_days:
        issues.append(
            f"Summe der Tage ({total}) übersteigt Monatslänge ({month_days})")
    for label, val in (("Arbeitstage", r.arbeitstage),
                       ("Urlaubstage", r.urlaubstage),
                       ("Krankheitstage", r.krankheitstage)):
        if val < 0:
            issues.append(f"{label} ist negativ: {val}")
        if val > month_days:
            issues.append(f"{label} übersteigt Monatslänge: {val}")

    return (len(issues) == 0), issues
