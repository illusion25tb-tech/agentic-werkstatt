"""Ein Worktree je Coder: eigenes Verzeichnis, eigener
Branch, aufgeräumt im finally."""
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


def _git(repo: Path, *args: str, check: bool = True) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True,
        text=True, encoding="utf-8", check=check).stdout


@contextmanager
def worktree(repo: Path, branch: str,
             base: str = "HEAD") -> Iterator[Path]:
    """Neuer Branch in eigenem Verzeichnis neben repo. Der
    Branch bleibt nach dem Aufräumen zum Ansehen stehen."""
    name = branch.replace("/", "-")
    path = repo.parent / f"{repo.name}--{name}"
    _git(repo, "worktree", "add", "-q", "-b", branch,
         str(path), base)
    try:
        yield path
    finally:
        # --force: auch mit ungesicherten Änderungen. Was
        # bleiben soll, hat der Orchestrator committet.
        _git(repo, "worktree", "remove", "--force", str(path),
             check=False)   # unter Windows evtl. gesperrt
        _git(repo, "worktree", "prune")
