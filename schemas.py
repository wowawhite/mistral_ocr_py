"""Pydantic-Datenmodelle: Ergebnis eines Seiten-Durchlaufs."""
from pydantic import BaseModel, Field


class FieldResult(BaseModel):
    """Ein erkanntes Textfeld mit Modell-Selbsteinschätzung."""
    value: str
    confidence: int = Field(default=0, ge=0, le=100)


class PageResult(BaseModel):
    """Strukturiertes Erkennungsergebnis einer Seite (1 Durchlauf)."""
    name: FieldResult
    datum: FieldResult
    arbeitstage: int = 0
    urlaubstage: int = 0
    krankheitstage: int = 0
    arbeitstage_conf: int = Field(default=0, ge=0, le=100)
    urlaubstage_conf: int = Field(default=0, ge=0, le=100)
    krankheitstage_conf: int = Field(default=0, ge=0, le=100)


class PageEvaluation(BaseModel):
    """Gesamtergebnis einer Seite inkl. Seiten-Konfidenz 0-100."""
    source_file: str
    result: PageResult
    page_confidence: int = Field(ge=0, le=100)
    quality_breakdown: dict = {}
    issues: list[str] = []

    @property
    def verdict(self) -> str:
        if self.page_confidence >= 90:
            return "GRUEN"
        if self.page_confidence >= 70:
            return "GELB"
        return "ROT"
