"""Hat der Coder nur Dateien berührt, die ihm gehören?
Gemessen mit git, nicht aus dem Bericht der Rolle."""
import subprocess
from fnmatch import fnmatch
from pathlib import Path

NEW_TESTS = "tests/test_*.py"   # neue Tests darf er anlegen


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "core.quotepath=false", *args],
        cwd=repo, capture_output=True, text=True,
        encoding="utf-8", check=True).stdout


def changed_files(repo: Path) -> dict[str, str]:
    """Pfad -> A (neu), M (geändert), D (gelöscht)."""
    out = _git(repo, "diff", "--name-status", "--no-renames",
               "HEAD")
    files = {p: s[0] for s, p in
             (z.split("\t", 1) for z in out.splitlines())}
    for p in _git(repo, "ls-files", "--others",
                  "--exclude-standard").splitlines():
        files[p] = "A"          # nicht angemeldet, trotzdem neu
    return files


def foreign(changed: dict[str, str],
            owned: list[str]) -> list[str]:
    """Dateien, die der Coder nicht hätte anfassen dürfen."""
    mine = {o.replace("\\", "/").removeprefix("./")
            for o in owned}
    return sorted(p for p, s in changed.items()
                  if p not in mine
                  and not (s == "A" and fnmatch(p, NEW_TESTS)))
