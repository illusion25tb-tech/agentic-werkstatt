"""Mini-Repository mit Fehler wie NL-107 und einer zweiten
Datei, die ein Planner fälschlich nennen kann."""
import json
import subprocess

import pytest
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import (
    ModelResponse,
    TextPart,
    ToolCallPart,
)
from pydantic_ai.models.function import FunctionModel

VERSAND = '''"""Gewichtsklassen, verkleinert."""


def klasse(kg: float) -> str:
    for name, grenze in (("S", 5.0), ("XL", 31.5)):
        if kg <= grenze:
            return name
    return "XL"
'''
LABELS = '''"""Labeltext, verkleinert."""


def label(klasse: str) -> str:
    return f"PF-{klasse}"
'''
ALT = '''from bestellservice.versand import klasse


def test_klein():
    assert klasse(2.0) == "S"
'''
PYPROJECT = '[tool.pytest.ini_options]\npythonpath = ["."]\n'


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True,
                          capture_output=True, text=True).stdout


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    (r / "tests").mkdir(parents=True)
    (r / "bestellservice").mkdir()
    for name, text in [
            ("bestellservice/__init__.py", ""),
            ("bestellservice/versand.py", VERSAND),
            ("bestellservice/labels.py", LABELS),
            ("tests/test_versand.py", ALT),
            ("pyproject.toml", PYPROJECT),
            (".gitignore", "__pycache__/\n")]:
        (r / name).write_bytes(text.encode())   # nur \n
    git(r, "init", "-q", "-b", "main")
    git(r, "config", "core.autocrlf", "false")
    git(r, "add", "-A")
    git(r, "-c", "user.name=t", "-c", "user.email=t@t",
        "commit", "-q", "-m", "Basis")
    return r


def skript(*schritte, seen=None):
    """Ein geskriptetes Modell je Rolle: Tupel = Tool Call,
    str = Text. seen sammelt, was das Modell zu sehen bekam."""
    it = iter(schritte)

    def antwort(messages, info) -> ModelResponse:
        if seen is not None:
            seen.append(messages)
        s = next(it, None)
        if s is None:
            raise UnexpectedModelBehavior("Skript zu Ende")
        part = TextPart(s) if isinstance(s, str) \
            else ToolCallPart(*s)
        return ModelResponse(parts=[part])
    return FunctionModel(antwort)


def j(**kw) -> str:
    return json.dumps(kw, ensure_ascii=False)
