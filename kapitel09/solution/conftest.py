"""Mini-Repository mit Fehler wie NL-107, per git init."""
import subprocess
import sys

import pytest

from deps import Deps
from diff_budget import Budget
from policy import Policy

VERSAND = '''"""Gewichtsklassen, verkleinert."""


def klasse(kg: float) -> str:
    for name, grenze in (("S", 5.0), ("XL", 31.5)):
        if kg <= grenze:
            return name
    return "XL"
'''
ALT = '''from bestellservice.versand import klasse


def test_klein():
    assert klasse(2.0) == "S"
'''
ACCEPT = '''from bestellservice.versand import klasse


def test_ueber_grenze_ist_sperrgut():
    assert klasse(38.0) == "SPERRGUT"
'''

PYPROJECT = '[tool.pytest.ini_options]\npythonpath = ["."]\n'


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True,
                   capture_output=True)


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    (r / "tests").mkdir(parents=True)
    (r / "bestellservice").mkdir()
    for name, text in [
            ("bestellservice/versand.py", VERSAND),
            ("tests/test_versand.py", ALT),
            ("tests/test_acceptance_x.py", ACCEPT),
            ("pyproject.toml", PYPROJECT),
            (".gitignore", "__pycache__/\n")]:
        (r / name).write_bytes(text.encode())   # nur \n
    git(r, "init", "-q", "-b", "main")
    git(r, "config", "core.autocrlf", "false")
    git(r, "add", "-A")
    git(r, "-c", "user.name=t", "-c", "user.email=t@t",
        "commit", "-q", "-m", "Basis")
    return r


@pytest.fixture
def deps(repo, tmp_path):
    return Deps(repo, Policy("interaktiv",
                             {"tests/test_versand.py"}),
                approve=lambda *a: True,
                budget=Budget(["bestellservice/*.py",
                               "tests/test_*.py"],
                              ["tests/test_acceptance_*.py"],
                              max_files=3, max_lines=20),
                trace=tmp_path / "trace.jsonl",
                python=sys.executable)
