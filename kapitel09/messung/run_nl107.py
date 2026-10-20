"""Echte Runs: Repo-Butler löst NL-107 in einer Arbeitskopie.

python run_nl107.py RUNS ARBEITSORDNER
Modell und Endpunkt aus LLM_MODEL, LLM_BASE_URL,
LLM_TEMPERATURE. Modus eval. Danach Prüfung mit dem
zurückgehaltenen Regressionstest aus NL-107.patch."""
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HIER = Path(__file__).resolve().parent
CODE = HIER.parents[1]
sys.path.insert(0, str(HIER.parent / "solution"))

import cli
from arbeitskopie import make_copy

PY = str(CODE / "bestellservice/.venv/Scripts/python.exe")


def hidden_test() -> str:
    patch = (CODE / "solutions/NL-107.patch").read_text("utf-8")
    teil = patch.split("+++ b/tests/test_nl107.py", 1)[1]
    teil = teil.split("\n", 2)[2]          # Hunk-Kopf weg
    return "\n".join(z[1:] for z in teil.splitlines()) + "\n"


def pytest_summary(repo: Path, *ziel: str) -> str:
    p = subprocess.run(
        [PY, "-m", "pytest", "-p", "no:cacheprovider",
         "--tb=no", "-o", "addopts=", "-q", *ziel],
        cwd=repo, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=300,
        check=False)
    zeilen = p.stdout.strip().splitlines()
    return zeilen[-1] if zeilen else p.stderr[-300:]


def one(i: int, work: Path) -> dict:
    out = HIER / "runs" / f"run_{i}"
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    repo = work / f"nl107_run_{i}_{int(time.time())}"
    make_copy(repo)
    issue = CODE / "issues/NL-107.md"
    t0 = time.time()
    code = cli.main([str(issue), "--repo", str(repo),
                     "--mode", "eval", "--python", PY,
                     "--out", str(out)], approve=None)
    dauer = round(time.time() - t0)
    diff = subprocess.run(
        ["git", "diff", "main", "--", "."], cwd=repo,
        capture_output=True, text=True, encoding="utf-8",
        check=True).stdout
    (out / "diff.patch").write_text(diff, encoding="utf-8")
    (repo / "tests/test_nl107_hidden.py").write_text(
        hidden_test(), encoding="utf-8")
    rec = {"run": i, "exit": code, "sekunden": dauer,
           "dateien": re.findall(r"^\+\+\+ b/(\S+)", diff, re.MULTILINE),
           "acceptance": pytest_summary(
               repo, "tests/test_acceptance_nl107.py"),
           "hidden": pytest_summary(
               repo, "tests/test_nl107_hidden.py"),
           "suite": pytest_summary(repo)}
    print(json.dumps(rec, ensure_ascii=False), flush=True)
    return rec


if __name__ == "__main__":
    runs, work = int(sys.argv[1]), Path(sys.argv[2])
    start = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    with (HIER / "ergebnisse.jsonl").open("a",
                                          encoding="utf-8") as f:
        for i in range(start, start + runs):
            f.write(json.dumps(one(i, work),
                               ensure_ascii=False) + "\n")
            f.flush()
