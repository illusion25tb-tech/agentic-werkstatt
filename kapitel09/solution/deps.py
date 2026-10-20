"""Was jeder Tool Call des Butlers mitbekommt."""
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from diff_budget import Budget
from policy import Policy

# Freigabefunktion: (Risiko, Tool, Argumente) -> ja/nein
Approve = Callable[[str, str, dict], bool]


@dataclass
class Deps:
    repo: Path                  # Arbeitskopie, Wurzel
    policy: Policy
    approve: Approve            # Terminal, Eval, später PR
    budget: Budget              # Diff-Budget aus Kapitel 7
    trace: Path                 # JSON Lines wie in Kapitel 4
    python: str = sys.executable    # Python mit pytest
    red_streak: int = 0         # rote Testläufe in Folge
    last_green: bool = False    # letzte volle Suite grün?
