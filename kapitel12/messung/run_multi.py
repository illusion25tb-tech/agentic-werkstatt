"""Planner, Coder, Reviewer auf dem Golden Task Set aus
Kapitel 10. Ergebniszeilen im Format von run_one.py, jede
sofort in results.jsonl, ein zweiter Aufruf setzt fort.

LLM_MODEL=llama3.2-16k LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_TEMPERATURE=0.7 python run_multi.py --runs 3
    --only NL-111,NL-113,NL-114,NL-118,NL-120

Die Rollen laufen nacheinander, nie zwei Modellaufrufe
gleichzeitig.
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

HIER = Path(__file__).resolve().parent
CODE = HIER.parents[1]
KAP12 = HIER.parent / "solution"
KAP10 = CODE / "kapitel10" / "solution"
sys.path[:0] = [str(KAP12), str(KAP10)]

import orchestrator  # setzt auch Kapitel 9 in den Pfad
from cli import model_from_env
from grade import git, grade
from metrics import cost, load_prices, metrics
from roles import ROLES
from run_one import BUDGET, _writable, fresh_copy, outcome
from run_suite import done
from tasks import load_tasks


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def versions(repo: Path) -> dict:
    """Wie run_one.versions, für Rollentexte und Orchestrator."""
    o = orchestrator
    md = repo / "AGENTS.md"
    text = (json.dumps(o.SYSTEM, ensure_ascii=False)
            + o.PLANNER_TASK + o.CODER_TASK + o.REVIEW_TASK
            + o.FORM + md.read_text(encoding="utf-8"))
    src = b"".join(
        p.read_bytes() for d in (o.BUTLER, KAP12)
        for p in sorted(d.glob("*.py"))
        if not p.name.startswith(("test_", "conf")))
    return {"prompt": _sha(text.encode()), "harness": _sha(src)}


def per_role(trace: Path) -> dict:
    """Token und Tool Calls je Rolle, Freigaben, Testläufe."""
    roles, reviews, tests = {}, [], []
    for z in trace.read_text(encoding="utf-8").splitlines():
        r = json.loads(z)
        s = roles.setdefault(r.get("role", "?"),
                             {"tokens": 0, "tool_calls": 0})
        s["tokens"] += (r.get("input_tokens", 0)
                        + r.get("output_tokens", 0))
        s["tool_calls"] += "tool" in r
        if "approve" in r:
            reviews.append(r["approve"])
        if r.get("role") == "tester":
            tests.append({"green": r["green"],
                          "changed": r["changed"]})
    return {"roles": roles, "reviews": reviews,
            "tester": tests}


def run_multi(task, run: int, *, source: Path, work: Path,
              out: Path, model, model_name: str, python: str,
              prices: dict, agents_md: Path) -> dict:
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
        rec["exit"] = orchestrator.Orchestrator(
            task.issue.read_text(encoding="utf-8"), task.id,
            repo, {r: model for r in ROLES}, python, d).run()
    except Exception as e:  # noqa: BLE001
        rec["exit"], rec["crash"] = None, repr(e)[:300]
    rec["seconds"] = round(time.time() - t0)
    rec["approved"] = rec["exit"] == 0
    branch = f"coder/{task.id}"
    if rec["exit"] != 0 and git(repo, "branch", "--list",
                                branch):
        git(repo, "switch", "-q", branch)   # wie Kap. 10:
    (d / "diff.patch").write_text(          # auch ungeprüft
        git(repo, "diff", task.base_commit), encoding="utf-8")
    rec |= grade(repo, task, python)
    trace = d / f"trace_{task.id}.jsonl"
    if trace.is_file():
        rec |= metrics(trace, task.expected_files)
        rec |= per_role(trace)
    rec["cost"] = cost(model_name, rec.get("input_tokens", 0),
                       rec.get("output_tokens", 0), prices)
    rec["over_budget"] = (rec["cost"] or 0) > BUDGET
    rec["outcome"] = outcome(rec)
    shutil.rmtree(repo, onexc=_writable)
    for rest in work.glob(f"{repo.name}--*"):  # Worktree-Reste
        shutil.rmtree(rest, onexc=_writable)
    return rec


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--only", default="")
    ap.add_argument("--out", type=Path,
                    default=HIER / "ergebnisse_multi")
    a = ap.parse_args(argv)
    os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
    tasks = load_tasks(CODE / "evals/tasks.json", CODE)
    if a.only:
        tasks = [t for t in tasks if t.id in a.only.split(",")]
    a.out.mkdir(parents=True, exist_ok=True)
    results = a.out / "results.jsonl"
    kw = {"source": CODE / "bestellservice",
          "out": a.out, "model": model_from_env(),
          "model_name": os.environ["LLM_MODEL"],
          "python": str(CODE / "bestellservice/.venv/Scripts"
                        / "python.exe"),
          "prices": load_prices(KAP10 / "prices.toml"),
          "agents_md": orchestrator.BUTLER
          / "fixtures/AGENTS_bestellservice.md"}
    fertig = done(results)
    with tempfile.TemporaryDirectory(
            ignore_cleanup_errors=True) as work:
        for i in range(1, a.runs + 1):     # erst Run 1 für alle
            for t in tasks:
                if (t.id, i) in fertig:
                    continue
                rec = run_multi(t, i, work=Path(work), **kw)
                with results.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False)
                            + "\n")
                print(t.id, i, rec["outcome"], rec["seconds"],
                      flush=True)


if __name__ == "__main__":
    main()
