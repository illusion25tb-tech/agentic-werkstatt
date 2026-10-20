"""NL-105: Plan und Diff-Vorschläge mit einem lokalen Modell.

Aufruf aus messung/ (Ollama lokal, nur llama3.2-16k):
  python run_nl105.py plan 3
  python run_nl105.py diff_roh 3
  python run_nl105.py diff_spec 3
Jede Zeile in ergebnisse.jsonl ist ein Run. Nichts wird auf
den bestellservice angewendet; git apply läuft nur mit --check.
"""
import json
import os
import sys
import time
from pathlib import Path

HIER = Path(__file__).parent
SOL = HIER.parent / "solution"
sys.path.insert(0, str(SOL))
cond = sys.argv[1]
runs = int(sys.argv[2]) if len(sys.argv) > 2 else 1
MODEL = "llama3.2-16k"
os.environ.update(LLM_BASE_URL="http://127.0.0.1:11434/v1",
                  LLM_MODEL=MODEL, LLM_TEMPERATURE="0.7",
                  LLM_JSON_MODE="0")

import agent_fc  # noqa: E402
import llm  # noqa: E402
import plan_mode  # noqa: E402
from diff_budget import Budget, check_diff, numstat  # noqa: E402
from plan_execute import LOCKED, applies  # noqa: E402
from repo_map import repo_map  # noqa: E402
from tools import ROOT  # noqa: E402

llm.TIMEOUT = 1800
SPEC = (SOL / "spec" / "NL-105.md").read_text(encoding="utf-8")
ISSUE = (ROOT.parent / "issues" / "NL-105.md").read_text(
    encoding="utf-8")
SCOPE = ["bestellservice/orders.py", "bestellservice/api.py",
         "bestellservice/models.py", "bestellservice/errors.py"]
CODE = "\n\n".join(
    f"=== {p} ===\n" + (ROOT / p).read_text(encoding="utf-8")
    for p in ("bestellservice/api.py", "bestellservice/orders.py"))
DIFF_AUFTRAG = """{auftrag}

Repo Map:
{karte}

Aktueller Code:
{code}

Antworte nur mit einem Unified Diff (--- a/pfad, +++ b/pfad,
@@-Köpfe), Pfade relativ zum Repository. Kein Text davor."""


def trace_usage(tr: Path) -> tuple[list[int], list]:
    recs = [json.loads(z) for z in tr.read_text(
        encoding="utf-8").splitlines()] if tr.exists() else []
    return [r["usage"].get("prompt_tokens", 0) for r in recs
            if r.get("usage")], recs


def run_plan(i: int) -> dict:
    tr = HIER / "traces" / f"plan_{i}.jsonl"
    tr.unlink(missing_ok=True)
    agent_fc.TRACE = tr
    plan_mode.PLAN_FILE = HIER / "traces" / f"plan_{i}.json"
    plan = plan_mode.make_plan(SPEC, SCOPE)
    pt, recs = trace_usage(tr)
    return dict(
        angenommen=plan is not None,
        schritte=len(plan.steps) if plan else 0,
        dateien=sorted({f for s in plan.steps for f in s.files})
        if plan else [],
        einwaende=[e for r in recs for e in r.get("rejected",
                                                  [])][:6],
        tool_calls=sum(1 for r in recs if "tool" in r),
        abbruch=next((r["abort"] for r in recs
                      if "abort" in r), None),
        max_prompt_tokens=max(pt, default=0))


def run_diff(i: int, roh: bool) -> dict:
    auftrag = (f"Issue:\n{ISSUE}" if roh else
               f"Setze diese Spezifikation um:\n{SPEC}")
    msg = DIFF_AUFTRAG.format(auftrag=auftrag, code=CODE,
                              karte=repo_map(ROOT))
    text = llm.ask_model([{"role": "user", "content": msg}])
    name = f"{'roh' if roh else 'spec'}_{i}.diff"
    (HIER / "traces" / name).write_text(text, encoding="utf-8")
    stat = numstat(text)
    tests = [p for p in stat if p.startswith("tests/")]
    return dict(
        datei=name, dateien=len(stat),
        zeilen=sum(a + r for a, r in stat.values()),
        ausserhalb=[p for p in stat if p not in SCOPE],
        tests=tests,
        budget=check_diff(text, Budget(SCOPE, LOCKED)),
        git_apply=applies(text, ROOT)[:2],
        prompt_tokens=llm.LAST_USAGE.get("prompt_tokens"),
        completion_tokens=llm.LAST_USAGE.get(
            "completion_tokens"))


(HIER / "traces").mkdir(exist_ok=True)
for i in range(runs):
    t0 = time.time()
    try:
        res = (run_plan(i) if cond == "plan"
               else run_diff(i, roh=cond == "diff_roh"))
    except Exception as e:  # noqa: BLE001
        res = {"exc": f"{type(e).__name__}: {e}"[:300]}
    rec = dict(cond=cond, model=MODEL, run=i,
               date=time.strftime("%Y-%m-%d"),
               sec=round(time.time() - t0), **res)
    print(json.dumps(rec, ensure_ascii=False), flush=True)
    with (HIER / "ergebnisse.jsonl").open(
            "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
