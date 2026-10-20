"""Antwortformat mit Belegen und der Verifizierer dazu."""
import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError

from contracts import ToolError
from read_lines import im_repo
from search_rg import search

VERWEIS = re.compile(r"\.\w+:\d+|\.(py|md|json|toml)$")


class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str
    path: str
    line_start: int
    line_end: int
    quote: str          # wörtlich aus den Zeilen


class Answer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claims: list[Claim] = []
    not_found: list[str] = []   # Suchmuster ohne Treffer


def _norm(s: str) -> str:
    return " ".join(s.split())


def check_claim(c: Claim, root: Path) -> str | None:
    """None, wenn der Beleg stimmt, sonst der Grund."""
    try:
        f = im_repo(c.path, root)
    except PermissionError as e:
        return str(e)
    if not f.is_file():
        return f"{c.path} gibt es nicht"
    lines = f.read_text(encoding="utf-8").splitlines()
    if not 1 <= c.line_start <= c.line_end <= len(lines):
        return (f"Zeilen {c.line_start}-{c.line_end} gibt es "
                f"in {c.path} nicht ({len(lines)} Zeilen)")
    bereich = "\n".join(lines[c.line_start - 1:c.line_end])
    if not c.quote.strip() or _norm(c.quote) not in _norm(
            bereich):
        return (f"Zitat steht nicht in {c.path}:"
                f"{c.line_start}-{c.line_end}")
    return None


def verify(raw: str, root: Path) -> list[str]:
    """Liste der Einwände; leer heißt: Antwort angenommen."""
    raw = raw[raw.find("{"):raw.rfind("}") + 1]  # ```json
    try:
        a = Answer.model_validate_json(raw)
    except ValidationError as e:
        err = e.errors()[0]
        return [f"Kein gültiges JSON: {err['msg']}, "
                + f"Feld {err['loc']}"]
    if not a.claims and not a.not_found:
        return ["Antwort ohne Beleg: claims oder not_found."]
    fehler = [f"Claim {i}: {grund}"
              for i, c in enumerate(a.claims, 1)
              if (grund := check_claim(c, root))]
    for muster in a.not_found:      # Harness sucht selbst
        if VERWEIS.search(muster) or len(muster.strip()) < 3:
            fehler.append(f"not_found {muster!r}: kein Suchbegriff."
                          " Nennen Sie, wonach Sie gesucht haben.")
            continue
        try:
            leer = search(muster, ".", root).startswith("Keine")
        except ToolError as e:
            leer, muster = False, f"{muster} ({e})"
        if not leer:
            fehler.append(f"not_found {muster!r}: es gibt "
                          "Treffer, search zeigt sie.")
    return fehler
