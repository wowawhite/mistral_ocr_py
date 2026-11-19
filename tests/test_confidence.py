from confidence import page_confidence
from schemas import FieldResult, PageResult


def sample():
    return PageResult(
        name=FieldResult(value="Ada", confidence=90),
        datum=FieldResult(value="01.01.2025", confidence=90),
        arbeitstage=20, urlaubstage=0, krankheitstage=0,
        arbeitstage_conf=90, urlaubstage_conf=90, krankheitstage_conf=90,
    )


def test_score_is_bounded_and_explained():
    score, parts = page_confidence(sample(), sample(), 0.8, True)
    assert 0 <= score <= 100
    assert set(parts) == {
        "modell_selbsteinschaetzung", "konsistenz_zweitdurchlauf",
        "plausibilitaet", "bildqualitaet",
    }
