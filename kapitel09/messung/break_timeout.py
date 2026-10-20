"""Break: subprocess.run(timeout=...) gegen run_capped().

Ein Kindprozess startet einen Enkel, der nach 4 s eine
Datei schreibt. Zeitlimit 2 s. Lebt der Enkel weiter?"""
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "solution"))
from tools_exec import run_capped

ENKEL = (
    "import subprocess, sys, time\n"
    "subprocess.Popen([sys.executable, '-c', 'import time;"
    " time.sleep(4); open(\"marker\", \"w\").close()'])\n"
    "time.sleep(60)\n")


def versuch(name: str, starte) -> None:
    with tempfile.TemporaryDirectory() as d:
        t0 = time.monotonic()
        starte(d)
        dauer = time.monotonic() - t0
        time.sleep(5)
        print(f"{name}: zurück nach {dauer:.1f} s, Enkel hat "
              f"geschrieben: {(Path(d) / 'marker').exists()}")


def nur_run(d: str) -> None:
    try:
        subprocess.run([sys.executable, "-c", ENKEL], cwd=d,
                       timeout=2, check=False)
    except subprocess.TimeoutExpired:
        pass


def run_mit_pipe(d: str) -> None:
    try:
        subprocess.run([sys.executable, "-c", ENKEL], cwd=d,
                       timeout=2, capture_output=True,
                       check=False)
    except subprocess.TimeoutExpired:
        pass


versuch("subprocess.run(timeout=2)", nur_run)
versuch("subprocess.run(timeout=2, capture_output=True)",
        run_mit_pipe)
versuch("run_capped(timeout=2)", lambda d: run_capped(
    [sys.executable, "-c", ENKEL], d, timeout=2))
