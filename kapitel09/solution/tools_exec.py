"""run_tests: zwei feste Befehle, ohne Shell, mit Zeitlimit.
Bei Zeitüberschreitung wird der ganze Prozessbaum beendet."""
import os
import signal
import subprocess

from deps import Deps
from read_lines import im_repo

TIMEOUT = 120               # Sekunden, Beispielwert
MAX_RED = 3                 # rote Läufe in Folge
WINDOWS = os.name == "nt"


class HandOver(Exception):
    """Der Butler gibt auf und übergibt an einen Menschen."""


def kill_tree(p: subprocess.Popen) -> None:
    if WINDOWS:     # /T: auch Kinder und Enkel, /F: sofort
        subprocess.run(["taskkill", "/T", "/F", "/PID",
                        str(p.pid)], capture_output=True,
                       check=False)  # Prozess evtl. schon weg
    else:           # eigene Session = eigene Prozessgruppe
        os.killpg(p.pid, signal.SIGKILL)


def run_capped(cmd: list[str], cwd, timeout: int = TIMEOUT):
    """(Exit-Code oder None, Ausgabe). Nur der direkte
    Kindprozess stirbt bei subprocess.run(timeout=...)."""
    p = subprocess.Popen(
        cmd, cwd=cwd, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True,
        encoding="utf-8", errors="replace",
        start_new_session=not WINDOWS)
    try:
        out = p.communicate(timeout=timeout)[0]
        return p.returncode, out
    except subprocess.TimeoutExpired:
        kill_tree(p)
        p.communicate()
        return None, f"Zeitlimit {timeout} s überschritten."


def short(out: str, keep: int = 8) -> str:
    """Fehlschläge und die letzten Zeilen, nicht alles."""
    lines = out.strip().splitlines()
    rot = [z for z in lines[:-keep]
           if z.startswith(("FAILED", "ERROR", "E ", "tests/"))]
    return "\n".join(rot[:10] + lines[-keep:])[-1500:]


def run_tests(deps: Deps, target: str = "tests") -> str:
    """Startet pytest für target unter tests/ und danach
    ruff check. Grün zählt nur für target="tests"."""
    rel = im_repo(target, deps.repo).relative_to(deps.repo)
    rel = rel.as_posix()
    if rel.split("/")[0] != "tests":
        raise ValueError("target muss unter tests/ liegen, "
                         "z. B. tests oder tests/test_x.py")
    code, out = run_capped(
        [deps.python, "-m", "pytest", "-q", "--tb=line",
         "-p", "no:cacheprovider", rel], deps.repo)
    lcode, lout = run_capped(
        [deps.python, "-m", "ruff", "check", "--no-cache",
         "."], deps.repo)
    green = code == 0 and lcode == 0
    deps.red_streak = 0 if green else deps.red_streak + 1
    deps.last_green = green and rel == "tests"
    if deps.red_streak >= MAX_RED:
        raise HandOver(f"{MAX_RED} rote Testläufe in Folge")
    ampel = {0: "grün"}
    return (f"pytest {ampel.get(code, 'ROT')}:\n{short(out)}"
            f"\nruff {ampel.get(lcode, 'ROT')}:\n"
            f"{short(lout, 4)}")
