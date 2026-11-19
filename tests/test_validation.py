from schemas import FieldResult, PageResult
from validation import check_plausibility, parse_datum


def valid_result(**overrides):
    data = dict(name=FieldResult(value="Max Mustermann", confidence=90),
                datum=FieldResult(value="15.03.2025", confidence=90),
                arbeitstage=20, urlaubstage=1, krankheitstage=0)
    data.update(overrides)
    return PageResult(**data)


def test_parse_valid_date():
    assert parse_datum("15.03.2025").isoformat() == "2025-03-15"


def test_reject_invalid_date():
    assert parse_datum("31.02.2025") is None


def test_valid_month_values():
    assert check_plausibility(valid_result())[0]


def test_reject_days_over_month_length():
    result = valid_result(arbeitstage=31, urlaubstage=1)
    ok, issues = check_plausibility(result)
    assert not ok
    assert any("Monatslänge" in issue for issue in issues)
