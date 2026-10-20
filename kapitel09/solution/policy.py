"""Approval Gates nach Risiko, nicht vor jedem Tool Call."""
from dataclasses import dataclass, field
from enum import StrEnum


class Risk(StrEnum):
    READ = "lesen"            # automatisch
    TEST = "testen"           # automatisch, mit Zeitlimit
    PLAN = "plan"             # Mensch bestätigt den Plan
    WRITE = "schreiben"       # Datei im Agenten-Branch
    PROTECTED = "testdatei"   # bestehender Test: gesondert
    COMMIT = "commit"         # erledigt der Harness


RISK = {"list_files": Risk.READ, "read_file": Risk.READ,
        "search": Risk.READ, "run_tests": Risk.TEST,
        "plan": Risk.PLAN, "replace_in_file": Risk.WRITE,
        "create_test": Risk.WRITE, "commit": Risk.COMMIT}
# push, PR, Löschen, Deploy: absichtlich keine Einträge
NEEDS_OK = {Risk.PLAN, Risk.WRITE, Risk.PROTECTED,
            Risk.COMMIT}
MODES = ("interaktiv", "eval", "nur_lesen")


@dataclass
class Policy:
    mode: str = "interaktiv"
    protected: set[str] = field(default_factory=set)
    asked: dict[str, int] = field(default_factory=dict)

    def risk(self, tool: str, args: dict) -> Risk | None:
        r = RISK.get(tool)
        if r is Risk.WRITE and args.get("path") in \
                self.protected:
            return Risk.PROTECTED
        return r

    def check(self, tool: str, args: dict,
              approve) -> str | None:
        """None heißt erlaubt, sonst der Grund für das Nein."""
        r = self.risk(tool, args)
        if r is None:
            return (f"{tool!r} ist kein Werkzeug des Butlers. "
                    "Push, PR, Löschen, Deploy: ein Mensch.")
        if self.mode == "nur_lesen" and r is not Risk.READ:
            return f"Modus nur_lesen: {r} ist gesperrt."
        if r not in NEEDS_OK:
            return None
        self.asked[r.value] = self.asked.get(r.value, 0) + 1
        if self.mode == "eval":         # zählen statt fragen
            if r is Risk.PROTECTED:
                return "Bestehender Test: im Eval-Modus tabu."
            return None
        if approve(r, tool, args):
            return None
        return f"{r}: vom Menschen abgelehnt."
