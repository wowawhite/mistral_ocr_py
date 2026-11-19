import pytest
from pydantic import ValidationError
from schemas import FieldResult, PageEvaluation, PageResult


def test_confidence_must_be_between_zero_and_hundred():
    with pytest.raises(ValidationError):
        FieldResult(value="x", confidence=101)


def test_page_evaluation_has_independent_mutable_defaults():
    first = PageEvaluation(source_file="a.jpg")
    second = PageEvaluation(source_file="b.jpg")
    first.issues.append("bad")
    assert second.issues == []
