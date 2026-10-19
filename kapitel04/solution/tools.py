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


def list_files(path: str = ".") -> str:
    base = _im_workspace(path)
    if not base.is_dir():
        raise FileNotFoundError(
            f"{path!r} ist kein Verzeichnis. Pfade ohne "
            "'workspace/' angeben, alles: list_files('.')")
    files = [p.relative_to(WORKDIR).as_posix()
             for p in base.rglob("*") if p.is_file()]
    return "\n".join(sorted(files)[:200]) or "(leer)"


def read_file(path: str) -> str:
    target = _im_workspace(path)
    if not target.is_file():
        raise FileNotFoundError(
            f"{path} gibt es nicht. Nutzen Sie list_files, "
            "um vorhandene Dateien zu sehen.")
    return target.read_text(encoding="utf-8")[:4000]


TOOLS = {"calculator": calculator, "read_file": read_file,
         "list_files": list_files}
