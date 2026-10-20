"""python inject.py faults.yaml

Spielt Störungen aus faults.yaml in die Rollen des Capstone
ein. Als Skript: Schema prüfen und Fälle auflisten."""
import sys
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel

KAP13 = Path(__file__).resolve().parents[2] / "kapitel13"
sys.path.append(str(KAP13 / "solution"))

from budget import BudgetExceeded  # Kapitel 13

DEP = ("\n--- a/pyproject.toml\n+++ b/pyproject.toml\n"
       '+    "{}",\n')


class Fault(BaseModel):
    id: str
    role: Literal["planner", "implementer", "tester",
                  "security", "release_reviewer"]
    effect: Literal["timeout", "red", "empty_diff",
                    "dependency", "budget"]
    value: str = ""


def load(path: Path) -> list[Fault]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [Fault(**f) for f in data["faults"]]


def inject(roles: dict, f: Fault) -> dict:
    """Kopie der Rollen, eine davon gestört."""
    inner = roles[f.role]

    def broken(arg):
        match f.effect:
            case "timeout":
                raise TimeoutError(f"{f.role} (injiziert)")
            case "budget":
                raise BudgetExceeded("cost_budget", "injiziert")
            case "red":
                return False
            case "empty_diff":
                return ""
            case "dependency":
                return inner(arg) + DEP.format(f.value)

    return {**roles, f.role: broken}


if __name__ == "__main__":
    for f in load(Path(sys.argv[1])):
        print(f.id, f.role, f.effect, f.value)
