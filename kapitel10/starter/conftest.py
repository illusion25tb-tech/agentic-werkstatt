"""Mini-Dienst mit Fehler wie NL-107 und eine Eval-Aufgabe
mit verstecktem Test, alles in tmp_path."""
import json

import pytest

from grade import git
from tasks import load_tasks

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
HIDDEN = '''from bestellservice.versand import klasse


def test_ueber_grenze_ist_sperrgut():
    assert klasse(38.0) == "SPERRGUT"
'''
FILES = {
    "bestellservice/__init__.py": "",
    "bestellservice/versand.py": VERSAND,
    "tests/test_versand.py": ALT,
    "pyproject.toml":
        '[tool.pytest.ini_options]\npythonpath = ["."]\n',
    ".gitignore": "__pycache__/\n"}


@pytest.fixture
def source(tmp_path):
    """Quelle wie code/bestellservice, noch ohne Git."""
    s = tmp_path / "service"
    for name, text in FILES.items():
        (s / name).parent.mkdir(parents=True, exist_ok=True)
        (s / name).write_bytes(text.encode())     # nur \n
    return s


@pytest.fixture
def task(tmp_path):
    root = tmp_path / "root"
    (root / "issues").mkdir(parents=True)
    (root / "evals/hidden").mkdir(parents=True)
    (root / "issues/NL-900.md").write_text(
        "Label für 38 kg hat den Standardtarif.",
        encoding="utf-8")
    (root / "evals/hidden/test_nl900.py").write_bytes(
        HIDDEN.encode())
    spec = {"tasks": [{
        "id": "NL-900", "issue": "issues/NL-900.md",
        "base_commit": "v1.0.0",
        "hidden_tests": ["evals/hidden/test_nl900.py"],
        "expected_files": ["bestellservice/versand.py"],
        "difficulty": 1, "ambiguous": False}]}
    (root / "evals/tasks.json").write_text(json.dumps(spec))
    return load_tasks(root / "evals/tasks.json", root)[0]


@pytest.fixture
def repo(source, tmp_path):
    """Git-Repository im Basisstand, Tag v1.0.0."""
    r = source
    git(r, "init", "-q", "-b", "main")
    git(r, "config", "core.autocrlf", "false")
    git(r, "add", "-A")
    git(r, "-c", "user.name=t", "-c", "user.email=t@t",
        "commit", "-q", "-m", "Basis")
    git(r, "tag", "v1.0.0")
    return r
