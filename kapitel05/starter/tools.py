"""Werkzeuge aus Kapitel 4, jetzt mit Vertrag."""
import subprocess
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from contracts import Registry, ToolError, ToolSpec

WORKDIR = Path("workspace").resolve()
ERLAUBT = set("0123456789+-*/(). ")


class Args(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CalcArgs(Args):
    expression: str = Field(
        max_length=200, description="z. B. 2*89.90 + 3*12.50")


class PathArgs(Args):
    path: str = Field(
        description="relativ, z. B. bestellungen/1.json")


class ListArgs(Args):
    path: str = Field(".", description="'.' für alle Dateien")


class GitArgs(Args):
    subcommand: Literal["status", "log", "diff", "show",
                        "ls-files", "grep"]
    args: list[str] = Field(
        [], description='z. B. ["HEAD~1", "HEAD"] oder ["-3"]')


def calculator(expression: str) -> str:
    if not set(expression) <= ERLAUBT or "**" in expression:
        raise ValueError(
            "Erlaubt sind Ziffern, + - * / ( ) und .")
    return str(eval(expression, {"__builtins__": {}}))


def _im_workspace(path: str, root: Path | None = None) -> Path:
    root = root or WORKDIR
    target = (root / path).resolve()
    if not target.is_relative_to(root):
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
             for p in base.rglob("*")
             if p.is_file() and ".git" not in p.parts]
    return "\n".join(sorted(files)[:200]) or "(leer)"


def read_file(path: str) -> str:
    target = _im_workspace(path)
    if not target.is_file():
        raise FileNotFoundError(
            f"{path} gibt es nicht. Nutzen Sie list_files, "
            "um vorhandene Dateien zu sehen.")
    return target.read_text(encoding="utf-8")[:4000]


GIT_OPTIONEN = {"-n", "-i", "-p", "-w", "-l", "--stat",
                "--oneline", "--name-only", "--"}
GIT_MIT_WERT = ("--format=", "--pretty=", "--grep=")


def git(subcommand: str, args: list[str]) -> str:
    for a in args:
        erlaubt = (a in GIT_OPTIONEN or a[1:].isdigit()
                   or a.startswith(GIT_MIT_WERT))
        if a.startswith("-") and not erlaubt:
            raise PermissionError(
                f"Option {a} ist nicht erlaubt. Erlaubt: "
                + " ".join(sorted(GIT_OPTIONEN))
                + " -<zahl> " + " ".join(GIT_MIT_WERT))
    cmd = ["git", "-c", "core.fsmonitor=false",
           "--no-pager", subcommand, *args]
    try:
        proc = subprocess.run(
            cmd, cwd=WORKDIR, capture_output=True, timeout=10,
            text=True, encoding="utf-8", errors="replace",
            check=False)
    except subprocess.TimeoutExpired:
        raise ToolError("timeout", "git brauchte über 10 s",
                        retryable=True) from None
    out = proc.stdout if proc.returncode == 0 else proc.stderr
    return out[:4000] or (
        "Befehl lief ohne Fehler, fand aber nichts. "
        "Pfade und Filter prüfen.")


ALL = [
    ToolSpec("calculator", "Rechnet mit + - * / ( ) und "
             "Dezimalpunkt. Keine Potenzen, keine Namen.",
             CalcArgs, calculator),
    ToolSpec("read_file", "Liest eine Textdatei im Workspace, "
             "höchstens 4.000 Zeichen. Fehler not_found: "
             "list_files zeigt vorhandene Dateien.",
             PathArgs, read_file),
    ToolSpec("list_files", "Listet Dateien unter path, "
             "höchstens 200.", ListArgs, list_files),
    ToolSpec("git", "Liest das Git-Repository des Workspace. "
             "Nur lesende Unterbefehle, Optionen nach "
             "Allowlist.",
             GitArgs, git),
]
TOOLS = Registry([s for s in ALL if s.read_only])
