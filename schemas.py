"""Validated data models for OCR results and batch evaluations."""
from pydantic import BaseModel, ConfigDict, Field, field_validator


class FieldResult(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    value: str = ""
    confidence: int = Field(default=0, ge=0, le=100)


class PageResult(BaseModel):
    name: FieldResult = Field(default_factory=FieldResult)
    datum: FieldResult = Field(default_factory=FieldResult)
    arbeitstage: int = Field(default=0, ge=0, le=31)
    urlaubstage: int = Field(default=0, ge=0, le=31)
    krankheitstage: int = Field(default=0, ge=0, le=31)
    arbeitstage_conf: int = Field(default=0, ge=0, le=100)
    urlaubstage_conf: int = Field(default=0, ge=0, le=100)
    krankheitstage_conf: int = Field(default=0, ge=0, le=100)


class PageEvaluation(BaseModel):
    source_file: str
    result: PageResult = Field(default_factory=PageResult)
    page_confidence: int = Field(default=0, ge=0, le=100)
    quality_breakdown: dict[str, float] = Field(default_factory=dict)
    issues: list[str] = Field(default_factory=list)
    status: str = "processed"
    error: str | None = None
    human_reviewed: bool = False

    @property
    def verdict(self) -> str:
        if self.status != "processed":
            return "ROT"
        if self.page_confidence >= 90:
            return "GRUEN"
        if self.page_confidence >= 70:
            return "GELB"
        return "ROT"
