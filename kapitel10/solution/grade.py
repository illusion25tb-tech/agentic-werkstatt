"""Bewerten nach dem Run, mit Tests, die der Agent nie sah."""
import shutil
import subprocess
from pathlib import Path

from tasks import Task


def git(repo: Path, *args: str) -> str:
    p = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True,
        text=True, encoding="utf-8", errors="replace",
        check=True)   # Git-Fehler sind hier Harness-Fehler
    return p.stdout


def pytest_ok(repo: Path, python: str, *targets: str) -> bool:
    p = subprocess.run(
        [python, "-m", "pytest", "-q", "--tb=no",
         "-p", "no:cacheprovider", "-o", "addopts=",
         *targets], cwd=repo, capture_output=True,
        timeout=600,
        check=False)   # rot ist ein Ergebnis, kein Fehler
    return p.returncode == 0


def grade(repo: Path, task: Task, python: str) -> dict:
    base = task.base_commit
    # Bestehende Tests geändert oder gelöscht? Neue sind ok.
    changed = git(repo, "diff", "--name-only",
                  "--diff-filter=MD", base, "--", "tests")
    # 1. Alle Testdateien zurück auf den Basisstand
    git(repo, "restore", f"--source={base}", "--staged",
        "--worktree", "--", "tests")
    git(repo, "clean", "-fdq", "--", "tests")
    # 2. Was vorher grün war, muss grün bleiben
    p2p = pytest_ok(repo, python, "tests")
    # 3. Versteckte Tests erst jetzt einspielen
    names = []
    for h in task.hidden_tests:
        shutil.copy(h, repo / "tests" / h.name)
        names.append(f"tests/{h.name}")
    f2p = pytest_ok(repo, python, *names)
    return {"resolved": f2p and p2p, "fail_to_pass": f2p,
            "pass_to_pass": p2p,
            "tests_changed": changed.split()}
