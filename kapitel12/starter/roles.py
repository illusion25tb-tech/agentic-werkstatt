"""Rollen als Verträge: Eingabe, Ausgabe, Tools, Budget."""
from dataclasses import dataclass

from pydantic import BaseModel, Field

READ = ("list_files", "read_file", "search")
WRITE = ("replace_in_file", "create_test", "run_tests")


class Plan(BaseModel):              # Planner -> Orchestrator
    steps: list[str] = Field(min_length=1)
    files: list[str] = Field(min_length=1)  # gehören dem Coder
    acceptance: list[str]           # was neue Tests prüfen


class PatchResult(BaseModel):       # misst der Orchestrator,
    changed: dict[str, str]         # nicht der Coder: git
    diff: str
    tests: str                      # Ausgabe pytest und Ruff
    green: bool


class Evidence(BaseModel):          # Testausgabe oder Zeile
    quote: str                      # wörtlich
    path: str = "tests"             # "tests" = Testausgabe
    line: int = 0


class Verdict(BaseModel):           # Reviewer -> Orchestrator
    approve: bool
    reason: str
    evidence: list[Evidence] = []   # noch freiwillig


@dataclass(frozen=True)
class Role:
    name: str
    tools: tuple[str, ...]          # Least Privilege je Rolle
    output: type[BaseModel] | None  # None: freier Text
    max_tool_calls: int             # Anteil am Gesamtbudget


ROLES = {r.name: r for r in (
    Role("planner", READ, Plan, 12),
    Role("coder", READ + WRITE, None, 12),
    Role("reviewer", READ, Verdict, 6))}
