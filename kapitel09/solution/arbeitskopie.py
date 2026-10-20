"""Meilenstein 1: Arbeitskopie des bestellservice anlegen.

python arbeitskopie.py ZIEL legt eine Kopie mit eigenem
Git-Repository an, dazu AGENTS.md und den Acceptance Test
für NL-107. Das Original bleibt unberührt."""
import shutil
import subprocess
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
QUELLE = HIER.parents[1] / "bestellservice"
WEG = shutil.ignore_patterns(".venv", "__pycache__",
                             ".pytest_cache", ".ruff_cache")


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True,
                   capture_output=True)


def make_copy(ziel: Path) -> Path:
    shutil.copytree(QUELLE, ziel, ignore=WEG)
    git(ziel, "init", "-q", "-b", "main")
    git(ziel, "config", "core.autocrlf", "false")
    git(ziel, "add", "-A")
    git(ziel, "-c", "user.name=Mensch", "-c",
        "user.email=mensch@nordlicht.invalid",
        "commit", "-q", "-m", "Basis v1.0.0")
    shutil.copy(HIER / "fixtures/AGENTS_bestellservice.md",
                ziel / "AGENTS.md")
    shutil.copy(HIER / "fixtures/test_acceptance_nl107.py",
                ziel / "tests")
    git(ziel, "add", "-A")
    git(ziel, "-c", "user.name=Mensch", "-c",
        "user.email=mensch@nordlicht.invalid", "commit",
        "-q", "-m", "NL-107: Acceptance Test, AGENTS.md")
    return ziel


if __name__ == "__main__":
    print(make_copy(Path(sys.argv[1]).resolve()))
