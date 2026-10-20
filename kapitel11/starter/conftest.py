"""Mini-Repository mit .env, dazu ein geskriptetes Modell."""
import subprocess

import pytest
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import (
    ModelResponse,
    TextPart,
    ToolCallPart,
)
from pydantic_ai.models.function import FunctionModel

KEY = "pf_attrappe_4f9c2b7e1d6a"        # nie ein echter Wert
FILES = {
    "bestellservice/__init__.py": "",
    "bestellservice/versand.py":
        'def klasse(kg: float) -> str:\n    return "XL"\n',
    "tests/test_versand.py":
        "from bestellservice.versand import klasse\n\n\n"
        "def test_xl():\n    assert klasse(20) == 'XL'\n",
    "README.md": "# Mini\n",
    "pyproject.toml":
        '[tool.pytest.ini_options]\npythonpath = ["."]\n',
    ".gitignore": "__pycache__/\n.env\n",
    ".env": f"PAKETFIX_KEY={KEY}\n",
}


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True,
                   capture_output=True)


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    for name, text in FILES.items():
        (r / name).parent.mkdir(parents=True, exist_ok=True)
        (r / name).write_bytes(text.encode())   # nur \n
    git(r, "init", "-q", "-b", "main")
    git(r, "add", "-A")                 # .env bleibt draußen
    git(r, "-c", "user.name=t", "-c", "user.email=t@t",
        "commit", "-q", "-m", "Basis")
    return r


def skript(*schritte):
    """Tool Calls als Tupel, Text als str (wie Kap. 9)."""
    it = iter(schritte)

    def antwort(messages, info) -> ModelResponse:
        s = next(it, None)
        if s is None:
            raise UnexpectedModelBehavior("Skript zu Ende")
        part = TextPart(s) if isinstance(s, str) \
            else ToolCallPart(*s)
        return ModelResponse(parts=[part])
    return FunctionModel(antwort)
