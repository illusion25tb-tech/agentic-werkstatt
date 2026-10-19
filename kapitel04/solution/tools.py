"""Werkzeuge des Agenten: Strings rein, String raus."""
import shlex
import subprocess
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


GIT_BEFEHLE = {"status", "log", "diff", "show", "ls-files",
               "grep"}
GIT_OPTIONEN = {"-n", "-i", "-p", "-w", "-l", "--stat",
                "--oneline", "--name-only", "--"}
GIT_MIT_WERT = ("--format=", "--pretty=", "--grep=")


def git(command: str) -> str:
    args = shlex.split(command)
    if args[:1] == ["git"]:
        args = args[1:]
    if not args or args[0] not in GIT_BEFEHLE:
        raise PermissionError(
            "Erlaubt sind nur: git "
            + ", ".join(sorted(GIT_BEFEHLE)))
    for a in args[1:]:
        erlaubt = (a in GIT_OPTIONEN or a[1:].isdigit()
                   or a.startswith(GIT_MIT_WERT))
        if a.startswith("-") and not erlaubt:
            raise PermissionError(
                f"Option {a} ist nicht erlaubt. Erlaubt: "
                + " ".join(sorted(GIT_OPTIONEN))
                + " -<zahl> " + " ".join(GIT_MIT_WERT))
    cmd = ["git", "-c", "core.fsmonitor=false",
           "--no-pager", *args]
    proc = subprocess.run(
        cmd, cwd=WORKDIR, capture_output=True, timeout=10,
        text=True, encoding="utf-8", errors="replace")
    out = proc.stdout if proc.returncode == 0 else proc.stderr
    return out[:4000] or (
        "Befehl lief ohne Fehler, fand aber nichts. "
        "Pfade und Filter prüfen.")


TOOLS = {"calculator": calculator, "read_file": read_file,
         "list_files": list_files, "git": git}
