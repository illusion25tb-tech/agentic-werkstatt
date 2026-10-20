"""python report.py ergebnisse/results.jsonl

Schreibt daneben report.md (für Menschen) und report.json.

report.json, Schema-Version 1. Dieses Format lesen
compare.py (Kap. 12), regression_alert.py (Kap. 13) und
eval_gate.py (Kap. 14). Quoten sind Anteile von 0 bis 1,
Kosten in der Währung von prices.toml.
{"schema": "agentic-werkstatt/eval-report", "version": 1,
 "k": Runs je Aufgabe (Minimum über alle Aufgaben),
 "versions": {"model": [...], "prompt": [...],
              "harness": [...]},
 "overall": {"runs": n, "resolved": c, "rate": c/n,
   "ci95": [unten, oben],        # Wilson, 95 %
   "pass_at_k": Mittel über Aufgaben,
   "pass_hat_k": Mittel über Aufgaben,
   "outcomes": {"gelöst": 4, "budget": 2, ...},
   "cost": {"mean": .., "stdev": ..} oder null (Preis fehlt),
   "tool_calls": {"mean": .., "stdev": ..},
   "asked": Summe, "policy": Summe,
   "tests_changed": Runs, "over_budget": Runs},
 "tasks": {"NL-111": {"runs": 3, "resolved": 1,
   "outcomes": ["gelöst", "falsch", "budget"],
   "pass_at_k": .., "pass_hat_k": .., "status": "wackelnd"}}}
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, stdev

from stats import pass_at_k, pass_hat_k, wilson


def spread(xs: list[float]) -> dict:
    sd = stdev(xs) if len(xs) > 1 else 0.0
    return {"mean": round(mean(xs), 4), "stdev": round(sd, 4)}


def status(n: int, c: int) -> str:
    if c == n:
        return "stabil gelöst"
    return "stabil gescheitert" if c == 0 else "wackelnd"


def per_task(rs: list[dict], k: int) -> dict:
    n, c = len(rs), sum(r["resolved"] for r in rs)
    rs = sorted(rs, key=lambda r: r["run"])
    return {"runs": n, "resolved": c,
            "outcomes": [r["outcome"] for r in rs],
            "pass_at_k": round(pass_at_k(n, c, k), 4),
            "pass_hat_k": round(pass_hat_k(n, c, k), 4),
            "status": status(n, c)}


def summarize(recs: list[dict]) -> dict:
    by = defaultdict(list)
    for r in recs:
        by[r["task"]].append(r)
    k = min(len(rs) for rs in by.values())
    tasks = {t: per_task(by[t], k) for t in sorted(by)}
    n, c = len(recs), sum(r["resolved"] for r in recs)
    costs = [r["cost"] for r in recs]
    return {
        "schema": "agentic-werkstatt/eval-report",
        "version": 1, "k": k,
        "versions": {f: sorted({r[f] for r in recs})
                     for f in ("model", "prompt", "harness")},
        "overall": {
            "runs": n, "resolved": c, "rate": round(c / n, 4),
            "ci95": [round(x, 4) for x in wilson(c, n)],
            "pass_at_k": round(mean(
                t["pass_at_k"] for t in tasks.values()), 4),
            "pass_hat_k": round(mean(
                t["pass_hat_k"] for t in tasks.values()), 4),
            "outcomes": dict(Counter(r["outcome"]
                                     for r in recs)),
            "cost": None if None in costs else spread(costs),
            "tool_calls": spread([r.get("tool_calls", 0)
                                  for r in recs]),
            "asked": sum(r.get("asked", 0) for r in recs),
            "policy": sum(r.get("policy", 0) for r in recs),
            "tests_changed": sum(bool(r["tests_changed"])
                                 for r in recs),
            "over_budget": sum(r["over_budget"] for r in recs)},
        "tasks": tasks}


def pct(x: float) -> str:
    return f"{x * 100:.0f} %"


def to_markdown(rep: dict) -> str:
    """Lesereihenfolge: Sicherheit, dann Erfolg, dann Kosten."""
    o, k, v = rep["overall"], rep["k"], rep["versions"]
    lo, hi = o["ci95"]
    tc = o["tool_calls"]
    kosten = "unbekannt (Preis fehlt)"
    if o["cost"] is not None:
        c = o["cost"]
        kosten = f"{c['mean']:.4f} ± {c['stdev']:.4f}"
    aus = ", ".join(f"{a} {m}"
                    for a, m in sorted(o["outcomes"].items()))
    zeilen = [
        "## Eval-Report", "",
        (f"Modell {', '.join(v['model'])}, Prompt "
         f"{', '.join(v['prompt'])}, Harness "
         f"{', '.join(v['harness'])}"), "",
        (f"1. Sicherheit: Policy-Verstöße {o['policy']}, "
         f"Runs mit geänderten Tests {o['tests_changed']}, "
         f"Freigabeanfragen {o['asked']}"),
        (f"2. Erfolg: {o['resolved']} von {o['runs']} gelöst, "
         f"{pct(o['rate'])} (95 %: {pct(lo)} bis {pct(hi)}), "
         f"pass@{k} {o['pass_at_k']:.2f}, "
         f"pass^{k} {o['pass_hat_k']:.2f}"),
        f"   Ausgänge: {aus}",
        (f"3. Kosten je Run: {kosten}, Runs über Budget "
         f"{o['over_budget']}; Tool Calls je Run: "
         f"{tc['mean']:.1f} ± {tc['stdev']:.1f}"), "",
        (f"| Issue | Ausgänge | gelöst | pass@{k} | pass^{k} |"
         " Status |"),
        "|---|---|---|---|---|---|"]
    for t, s in rep["tasks"].items():
        zeilen.append(
            f"| {t} | {', '.join(s['outcomes'])} | "
            f"{s['resolved']}/{s['runs']} | "
            f"{s['pass_at_k']:.2f} | {s['pass_hat_k']:.2f} | "
            f"{s['status']} |")
    return "\n".join(zeilen) + "\n"


def main(results: Path) -> dict:
    recs = [json.loads(z) for z in results.read_text(
        encoding="utf-8").splitlines() if z.strip()]
    rep = summarize(recs)
    (results.parent / "report.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=1),
        encoding="utf-8")
    (results.parent / "report.md").write_text(
        to_markdown(rep), encoding="utf-8")
    return rep


if __name__ == "__main__":
    main(Path(sys.argv[1]))
