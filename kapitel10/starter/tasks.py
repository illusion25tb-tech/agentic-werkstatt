"""Golden Task Set laden: evals/tasks.json, geprüft."""
import json
from dataclasses import dataclass
from pathlib import Path

PFLICHT = ("id", "issue", "base_commit", "hidden_tests",
           "expected_files", "difficulty", "ambiguous")


@dataclass(frozen=True)
class Task:
    id: str
    issue: Path              # Ticket-Text, der Agent sieht ihn
    base_commit: str         # Stand, auf dem jeder Run startet
    hidden_tests: list[Path]  # sieht der Agent nie
    expected_files: list[str]  # für die Exploration
    difficulty: int          # 1 leicht bis 3 schwer
    ambiguous: bool          # absichtlich mehrdeutig


def load_tasks(path: Path, root: Path) -> list[Task]:
    """root: Wurzel, zu der issue und hidden_tests relativ
    sind (im Begleit-Repository der Ordner code/)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    tasks = []
    for t in data["tasks"]:
        fehlt = [k for k in PFLICHT if k not in t]
        if fehlt:
            raise ValueError(f"{t.get('id')}: fehlt {fehlt}")
        tasks.append(Task(
            t["id"], root / t["issue"], t["base_commit"],
            [root / h for h in t["hidden_tests"]],
            t["expected_files"], t["difficulty"],
            t["ambiguous"]))
    return tasks
