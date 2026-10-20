"""Zeilenbereich mit Nummern lesen, statt ganzer Dateien."""
from pathlib import Path

from contracts import ToolError

MAX_LINES = 60


def im_repo(path: str, root: Path) -> Path:
    """Pfadprüfung aus Kapitel 4, Wurzel ist das Repository."""
    target = (root / path).resolve()
    if not target.is_relative_to(root):
        raise PermissionError(
            f"{path} liegt außerhalb des Repos")
    return target


def read_lines(path: str, start: int, end: int,
               root: Path) -> str:
    target = im_repo(path, root)
    if not target.is_file():
        raise FileNotFoundError(
            f"{path} gibt es nicht. search oder die Repo Map "
            "zeigen vorhandene Dateien.")
    lines = target.read_text(encoding="utf-8").splitlines()
    if not 1 <= start <= min(end, len(lines)):
        raise ToolError("invalid_args",
                        f"Bereich {start}-{end} ungültig, "
                        f"{path} hat {len(lines)} Zeilen.")
    end = min(end, start + MAX_LINES - 1, len(lines))
    return "\n".join(f"{n:4}| {lines[n - 1]}"
                     for n in range(start, end + 1))
