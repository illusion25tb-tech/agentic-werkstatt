"""Der Vertrag für das Ergebnis des Issue-Klassifizierers."""
import json
from typing import Literal

from pydantic import BaseModel, Field


class IssueKlasse(BaseModel):
    kategorie: Literal["bug", "feature", "frage", "sicherheit"]
    prioritaet: Literal["niedrig", "mittel", "hoch"]
    begruendung: str = Field(min_length=10, max_length=300)
    dateien: list[str] = []


if __name__ == "__main__":
    schema = IssueKlasse.model_json_schema()
    print(json.dumps(schema, indent=2, ensure_ascii=False))
