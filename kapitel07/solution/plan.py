"""Plan als Datenstruktur und seine Prüfung im Harness."""
from graphlib import CycleError, TopologicalSorter
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

CHECKS = ("pytest ", "ruff check ")   # ohne Modell entscheidbar


class Step(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    goal: str
    files: list[str] = Field(min_length=1)
    check: str
    depends_on: list[str] = []


class Plan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    goal: str
    steps: list[Step] = Field(min_length=1)


def check_plan(plan: Plan, root: Path) -> list[str]:
    """Einwände gegen den Plan; leer heißt: prüfbar."""
    fehler, ids = [], {s.id for s in plan.steps}
    for s in plan.steps:
        for f in s.files:
            p = (root / f).resolve()
            if not (p.is_relative_to(root) and p.is_file()):
                fehler.append(f"{s.id}: {f} gibt es nicht")
        if not s.check.startswith(CHECKS):
            fehler.append(f"{s.id}: check {s.check!r} ist kein "
                          "Befehl mit " + " oder ".join(CHECKS))
        for d in set(s.depends_on) - ids:
            fehler.append(f"{s.id}: hängt von {d!r} ab, den "
                          "Schritt gibt es nicht")
    graph = {s.id: set(s.depends_on) for s in plan.steps}
    try:
        tuple(TopologicalSorter(graph).static_order())
    except CycleError as e:
        fehler.append(f"Zyklus: {' -> '.join(e.args[1])}")
    return fehler


def order(plan: Plan) -> list[Step]:
    """Schritte so, dass Abhängigkeiten zuerst kommen."""
    graph = {s.id: set(s.depends_on) for s in plan.steps}
    by_id = {s.id: s for s in plan.steps}
    return [by_id[i] for i in
            TopologicalSorter(graph).static_order()]
