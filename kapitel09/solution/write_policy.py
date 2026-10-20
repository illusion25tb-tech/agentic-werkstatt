"""Schreibregel: was ins Episoden-Memory darf (Harden)."""
import re
from pathlib import Path

from memory import record

MAX_DAYS = 90
ANWEISUNG = re.compile(     # Heuristik, allein kein Schutz
    r"hinweis für agent|ignorier|überspring|nicht mehr lesen",
    re.IGNORECASE)


def _kopiert(lesson: str, observations: list[str]) -> bool:
    """Steht eine Folge von 6 Wörtern wörtlich in einer
    Observation? Dann hat das Modell nur abgeschrieben."""
    w = lesson.split()
    obs = [" ".join(o.split()) for o in observations]
    return any(" ".join(w[i:i + 6]) in o
               for o in obs for i in range(len(w) - 5))


def check(ep: dict, root: Path,
          observations: list[str] = ()) -> list[str]:
    """Leere Liste heißt: darf gespeichert werden."""
    fehler = []
    if not ep.get("source"):
        fehler.append("Quelle fehlt")
    if not ep.get("verified"):
        fehler.append("Ausgang nicht vom Harness geprüft")
    if not 0 < ep.get("days", 0) <= MAX_DAYS:
        fehler.append(f"Ablauf fehlt oder > {MAX_DAYS} Tage")
    for f in ep.get("files", []):
        if not (root / f).is_file():
            fehler.append(f"{f} gibt es nicht")
    if ANWEISUNG.search(ep.get("lesson", "")):
        fehler.append("Lehre enthält eine Anweisung")
    if _kopiert(ep.get("lesson", ""), list(observations)):
        fehler.append("Lehre ist aus einer Observation kopiert")
    return fehler


def remember(conn, ep: dict, root: Path,
             observations: list[str] = ()) -> int:
    """Einziger Schreibweg ins Memory nach dem Harden."""
    fehler = check(ep, root, observations)
    if fehler:
        raise ValueError("; ".join(fehler))
    return record(conn, **ep)
