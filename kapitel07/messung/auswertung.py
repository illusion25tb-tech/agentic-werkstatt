"""Prüft die gespeicherten Diff-Vorschläge mit dem Endstand
von diff_budget.py und plan_execute.applies() erneut."""
import json
import sys
from pathlib import Path

HIER = Path(__file__).parent
sys.path.insert(0, str(HIER.parent / "solution"))

from diff_budget import Budget, check_diff, numstat  # noqa: E402
from plan_execute import LOCKED, applies  # noqa: E402
from tools import ROOT  # noqa: E402

SCOPE = ["bestellservice/orders.py", "bestellservice/api.py",
         "bestellservice/models.py", "bestellservice/errors.py"]

for f in sorted((HIER / "traces").glob("*.diff")):
    text = f.read_text(encoding="utf-8")
    stat = numstat(text)
    print(f.name, json.dumps(stat), "|",
          check_diff(text, Budget(SCOPE, LOCKED)), "|",
          applies(text, ROOT))
for line in (HIER / "ergebnisse.jsonl").read_text(
        encoding="utf-8").splitlines():
    r = json.loads(line)
    if r["cond"] == "plan":
        print("plan", r["run"], r["angenommen"], r["schritte"],
              r["tool_calls"], r["abbruch"], r["max_prompt_tokens"])
