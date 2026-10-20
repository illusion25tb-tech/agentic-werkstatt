"""Meilenstein 2: Was jeder Tool Call des Explorers bekommt.
Policy, Freigabe und Budget kommen in solution/ dazu."""
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Deps:
    repo: Path                  # Arbeitskopie, Wurzel
    trace: Path                 # JSON Lines wie in Kapitel 4
