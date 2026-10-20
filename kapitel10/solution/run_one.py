"""Ein Run: frische Kopie, Butler im Eval-Modus, Bewertung,
Kennzahlen und Versionen als eine Ergebniszeile."""
import hashlib
import os
import shutil
import stat
import sys
import time
from pathlib import Path

HIER = Path(__file__).resolve().parent
BUTLER = HIER.parents[1] / "kapitel09" / "solution"
sys.path.insert(0, str(BUTLER))        # Repo-Butler, Kap. 9

import agent
import cli

from grade import git, grade
from metrics import cost, metrics

BUDGET = 0.50     # je Run, Beispielwert, Währung der Preise
WEG = shutil.ignore_patterns(".venv", "__pycache__",
                             ".pytest_cache", ".ruff_cache")
EVAL = ["-c", "user.name=Eval", "-c",
        "user.email=eval@nordlicht.invalid"]


def fresh_copy(src: Path, dest: Path, base: str,
               agents_md: Path | None) -> Path:
    """Kopie im Basisstand mit eigenem Git und Tag base."""
    shutil.copytree(src, dest, ignore=WEG)
    if agents_md:
        shutil.copy(agents_md, dest / "AGENTS.md")
    git(dest, "init", "-q", "-b", "main")
    git(dest, "config", "core.autocrlf", "false")
    git(dest, "add", "-A")
    git(dest, *EVAL, "commit", "-q", "-m", "Basis")
    git(dest, "tag", base)
    return dest


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def versions(repo: Path) -> dict:
    """Prompt-Version: Systemtext, Formauftrag, AGENTS.md.
    Harness-Version: Quelltext des Butlers ohne Tests."""
    md = repo / "AGENTS.md"
    text = agent.SYSTEM + agent.FORM + (
        md.read_text(encoding="utf-8") if md.is_file() else "")
    src = b"".join(p.read_bytes()
                   for p in sorted(BUTLER.glob("*.py"))
                   if not p.name.startswith(("test_", "conf")))
    return {"prompt": _sha(text.encode()), "harness": _sha(src)}


def outcome(rec: dict) -> str:
    if rec["exit"] is None:      # Fehler im Harness:
        return "absturz"         # vor allem anderen ansehen
    if rec["resolved"]:
        return "gelöst"
    abort = rec.get("abort") or ""
    if abort.startswith("UsageLimitExceeded"):
        return "budget"
    return "übergabe" if rec["exit"] == 2 else "falsch"


def run_one(task, run: int, *, source: Path, work: Path,
            out: Path, model, model_name: str, python: str,
            prices: dict, agents_md: Path | None) -> dict:
    d = out / task.id / f"run_{run}"
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    repo = fresh_copy(source, work / f"{task.id}_{run}",
                      task.base_commit, agents_md)
    rec = {"task": task.id, "run": run, "model": model_name,
           "seed": None, **versions(repo),
           "started": time.strftime("%Y-%m-%dT%H:%M:%S")}
    t0 = time.time()
    try:
        rec["exit"] = cli.main(
            [str(task.issue), "--repo", str(repo), "--mode",
             "eval", "--python", python, "--out", str(d)],
            approve=None, model=model)
    except Exception as e:  # noqa: BLE001
        rec["exit"], rec["crash"] = None, repr(e)[:300]
    rec["seconds"] = round(time.time() - t0)
    (d / "diff.patch").write_text(
        git(repo, "diff", task.base_commit), encoding="utf-8")
    rec |= grade(repo, task, python)
    trace = d / f"trace_{task.issue.stem}.jsonl"
    if trace.is_file():
        rec |= metrics(trace, task.expected_files)
    rec["cost"] = cost(model_name, rec.get("input_tokens", 0),
                       rec.get("output_tokens", 0), prices)
    rec["over_budget"] = (rec["cost"] or 0) > BUDGET
    rec["outcome"] = outcome(rec)
    shutil.rmtree(repo, onexc=_writable)
    return rec


def _writable(func, path, exc) -> None:
    os.chmod(path, stat.S_IWRITE)   # Git-Objekte unter Windows
    func(path)
