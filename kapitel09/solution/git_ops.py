"""Git als Sicherheitsnetz. Der Harness ruft das, nie das
Modell: Es gibt kein Tool für push, reset oder switch."""
import subprocess
from pathlib import Path

ICH = ["-c", "user.name=Repo-Butler",
       "-c", "user.email=butler@nordlicht.invalid"]


class DirtyTree(Exception):
    pass


def git(repo: Path, *args: str) -> str:
    p = subprocess.run(
        ["git", "-c", "core.fsmonitor=false", *args],
        cwd=repo, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=30,
        check=True)   # Git-Fehler hier sind Harness-Fehler
    return p.stdout


def start(repo: Path, issue: str) -> str:
    """Prüft den sauberen Baum, legt butler/<issue> an und
    gibt den Ausgangsbranch zurück."""
    if git(repo, "status", "--porcelain"):
        raise DirtyTree("Arbeitsbaum nicht sauber. Erst "
                        "committen oder stashen.")
    base = git(repo, "branch", "--show-current").strip()
    git(repo, "switch", "-q", "-c", f"butler/{issue}")
    return base


def diff(repo: Path) -> str:
    """Alle Änderungen seit dem letzten Commit, auch neue
    Dateien, die mit git add -N angemeldet sind."""
    return git(repo, "diff", "HEAD")


def commit(repo: Path, message: str) -> str:
    git(repo, "add", "-A")
    git(repo, *ICH, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "--short", "HEAD").strip()


def discard(repo: Path, base: str, issue: str) -> None:
    """Vollständiges Rückgängig: Änderungen, neue Dateien
    und den Branch des Butlers verwerfen."""
    git(repo, "reset", "-q", "--hard")
    git(repo, "clean", "-q", "-fd")
    git(repo, "switch", "-q", base)
    git(repo, "branch", "-q", "-D", f"butler/{issue}")
