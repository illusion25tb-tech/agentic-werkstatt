"""Werkzeuge des Agenten: Strings rein, String raus."""
from pathlib import Path

WORKDIR = Path("workspace").resolve()
ERLAUBT = set("0123456789+-*/(). ")


def calculator(expression: str) -> str:
    if not set(expression) <= ERLAUBT or "**" in expression:
        raise ValueError(
            "Erlaubt sind Ziffern, + - * / ( ) und .")
    return str(eval(expression, {"__builtins__": {}}))


def _im_workspace(path: str) -> Path:
    target = (WORKDIR / path).resolve()
    if not target.is_relative_to(WORKDIR):
        raise PermissionError(
            f"{path} liegt außerhalb des Workspace")
    return target


def read_file(path: str) -> str:
    text = _im_workspace(path).read_text(encoding="utf-8")
    return text[:4000]


TOOLS = {"calculator": calculator, "read_file": read_file}
