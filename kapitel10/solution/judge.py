"""LLM-as-a-Judge für die Begründung im ButlerReport.
Nur ergänzend: Ob der Patch stimmt, sagen die Tests."""
from pydantic import BaseModel, Field, ValidationError

RUBRIK = """Du bewertest die Begründung zu einem Patch.
Skala, nur ganze Zahlen:
1 = fehlt oder widerspricht dem Diff
2 = nennt die Änderung, aber nicht die Ursache
3 = Ursache und Änderung, Belege passen zum Diff
4 = wie 3, dazu Grenzen oder Risiken benannt
Erst begründen, mit Bezug auf eine Zeile des Diffs,
dann die Zahl. Antworte nur mit JSON:
{"reason": "...", "score": 1}"""


class Verdict(BaseModel):
    reason: str = Field(min_length=20)
    score: int = Field(ge=1, le=4)


def judge(ask, begruendung: str, diff: str) -> Verdict | None:
    """ask: ask_model aus Kapitel 3. None heißt: kein
    gültiges Urteil, zählt weder als gut noch als schlecht."""
    msgs = [{"role": "system", "content": RUBRIK},
            {"role": "user", "content":
             f"Diff:\n{diff}\n\nBegründung:\n{begruendung}"}]
    try:
        return Verdict.model_validate_json(ask(msgs))
    except ValidationError:
        return None
