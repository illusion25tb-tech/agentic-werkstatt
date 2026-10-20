"""Ablauf des Agentic Release Engineer, ohne Modell.

Rollen sind Funktionen: Planner, Implementer und Release
Reviewer rufen im echten Einsatz ein Modell (Kapitel 12),
Tester und Security Reviewer sind Code. Das Ergebnis ist
eine Empfehlung oder eine Eskalation an einen Menschen.
Ausrollen kommt in diesem Modul nicht vor (Kapitel 14)."""
import re
from dataclasses import dataclass, field

# ponytail: feste Liste; im Repository aus der Lock-Datei
ALLOWED = {"fastapi", "pydantic", "httpx", "pytest", "ruff"}


class Escalate(Exception):
    """Ein Mensch muss entscheiden."""


@dataclass
class Outcome:
    result: str                 # "empfehlung" | "eskalation"
    reason: str = ""
    trail: list[str] = field(default_factory=list)


def new_deps(diff: str) -> list[str]:
    """Neue Zeilen in pyproject.toml, die kein bekanntes
    Paket nennen. Streng: jede unbekannte Zeile zählt."""
    out, pp = [], False
    for line in diff.splitlines():
        if line.startswith("+++ "):
            pp = line.endswith("pyproject.toml")
        elif pp and line.startswith("+"):
            text = line[1:].strip(' ",')
            name = re.split(r"[<>=!~\[ ]", text)[0]
            if name and name.lower() not in ALLOWED:
                out.append(name)
    return out


def security_review(diff: str) -> list[str]:
    """Security Reviewer als Code: Befunde, leer = ok."""
    found = [f"Test geändert: {z[6:]}"
             for z in diff.splitlines()
             if z.startswith("--- a/tests/")]
    found += [f"neue Abhängigkeit: {d}" for d in new_deps(diff)]
    return found


def release(issue: str, roles: dict) -> Outcome:
    trail: list[str] = []
    try:
        plan = roles["planner"](issue)
        trail.append("planner")
        diff = roles["implementer"](plan)
        trail.append("implementer")
        if not diff.strip():            # Kapitel 10 und 12
            raise Escalate("leerer Diff")
        if not roles["tester"](diff):
            raise Escalate("Tests rot")
        trail.append("tester")
        if found := roles["security"](diff):
            raise Escalate("; ".join(found))
        trail.append("security")
        note = roles["release_reviewer"](diff)
        trail.append("release_reviewer")
    except Escalate as e:
        return Outcome("eskalation", str(e), trail)
    except Exception as e:  # noqa: BLE001
        why = f"{type(e).__name__}: {e}"
        return Outcome("eskalation", why, trail)
    return Outcome("empfehlung", note, trail)
