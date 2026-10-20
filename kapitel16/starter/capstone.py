"""Ablauf des Agentic Release Engineer, ohne Modell.

Rollen sind Funktionen: Planner, Implementer und Release
Reviewer rufen im echten Einsatz ein Modell (Kapitel 12),
Tester und Security Reviewer sind Code. Das Ergebnis ist
eine Empfehlung oder eine Eskalation an einen Menschen.
Ausrollen kommt in diesem Modul nicht vor (Kapitel 14)."""
from dataclasses import dataclass, field


class Escalate(Exception):
    """Ein Mensch muss entscheiden."""


@dataclass
class Outcome:
    result: str                 # "empfehlung" | "eskalation"
    reason: str = ""
    trail: list[str] = field(default_factory=list)


def security_review(diff: str) -> list[str]:
    """Security Reviewer als Code: Befunde, leer = ok."""
    return [f"Test geändert: {z[6:]}"
            for z in diff.splitlines()
            if z.startswith("--- a/tests/")]


def release(issue: str, roles: dict) -> Outcome:
    trail: list[str] = []
    try:
        plan = roles["planner"](issue)
        trail.append("planner")
        diff = roles["implementer"](plan)
        trail.append("implementer")
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
