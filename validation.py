"""Validation of extracted fields and configurable business constraints."""
import re
from datetime import date
from schemas import PageResult

DATE_RE = re.compile(r"^\s*(\d{1,2})\.(\d{1,2})\.(\d{4})\s*$")


def parse_datum(value: str) -> date | None:
    match = DATE_RE.match(value or "")
    if not match:
        return None
    try:
        day, month, year = (int(part) for part in match.groups())
        return date(year, month, day)
    except ValueError:
        return None


def check_plausibility(result: PageResult, *, allow_future: bool = False,
                       min_year: int = 2000) -> tuple[bool, list[str]]:
    issues: list[str] = []
    if not result.name.value.strip():
        issues.append("Name ist leer")
    if result.name.confidence == 0:
        issues.append("Name nicht lesbar erkannt")

    parsed = parse_datum(result.datum.value)
    if parsed is None:
        issues.append(f"Datum nicht parsebar: '{result.datum.value}'")
        month_days = 31
    else:
        if not allow_future and parsed > date.today():
            issues.append(f"Datum liegt in der Zukunft: {parsed:%d.%m.%Y}")
        if parsed.year < min_year:
            issues.append(f"Datum unplausible Jahreszahl: {parsed.year}")
        month_days = __import__("calendar").monthrange(parsed.year, parsed.month)[1]

    values = (("Arbeitstage", result.arbeitstage),
              ("Urlaubstage", result.urlaubstage),
              ("Krankheitstage", result.krankheitstage))
    for label, value in values:
        if value < 0:
            issues.append(f"{label} ist negativ: {value}")
        if value > month_days:
            issues.append(f"{label} übersteigt Monatslänge: {value}")
    if sum(value for _, value in values) > month_days:
        issues.append(f"Summe der Tage ({sum(v for _, v in values)}) übersteigt Monatslänge ({month_days})")
    return not issues, issues
