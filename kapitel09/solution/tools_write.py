"""Schreibende Tools: kleine Änderungen, Budget im Tool."""
from fnmatch import fnmatch

import git_ops
from deps import Deps
from diff_budget import check_diff
from read_lines import im_repo


def _within_budget(deps: Deps, undo) -> None:
    fehler = check_diff(git_ops.diff(deps.repo), deps.budget)
    if fehler:
        undo()                  # Änderung zurücknehmen
        raise ValueError("Zurückgenommen: " + "; ".join(fehler))


def replace_in_file(deps: Deps, path: str, old: str,
                    new: str) -> str:
    """Ersetzt den Text old durch new. old muss genau einmal
    in der Datei stehen, wörtlich mit Einrückung."""
    target = im_repo(path, deps.repo)
    if not target.is_file():
        raise FileNotFoundError(
            f"{path} gibt es nicht. Neue Tests: create_test.")
    raw = target.read_bytes()
    crlf = b"\r\n" in raw       # Windows-Zeilenenden merken
    text = raw.decode("utf-8").replace("\r\n", "\n")
    n = text.count(old) if old else 0
    if n != 1:
        raise ValueError(
            f"old steht {n}-mal in {path}, verlangt ist genau "
            "einmal. Stelle mit read_file lesen und old "
            "wörtlich mit einer Zeile mehr Kontext angeben.")
    text = text.replace(old, new)
    if crlf:
        text = text.replace("\n", "\r\n")
    target.write_bytes(text.encode("utf-8"))
    _within_budget(deps, lambda: target.write_bytes(raw))
    return f"{path}: geändert. Jetzt run_tests aufrufen."


def create_test(deps: Deps, path: str, content: str) -> str:
    """Legt eine NEUE Testdatei tests/test_<name>.py an."""
    target = im_repo(path, deps.repo)
    if not fnmatch(path, "tests/test_*.py"):
        raise ValueError("Nur neue Dateien tests/test_*.py.")
    if target.exists():
        raise FileExistsError(
            f"{path} gibt es schon. Anderen Namen wählen.")
    target.write_bytes(content.encode("utf-8"))
    git_ops.git(deps.repo, "add", "-N", path)  # für den Diff
    _within_budget(deps, lambda: (
        git_ops.git(deps.repo, "rm", "-q", "--cached", path),
        target.unlink()))
    return f"{path}: angelegt. Jetzt run_tests aufrufen."
