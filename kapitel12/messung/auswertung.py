"""Baseline aus Kapitel 10 auf dieselben Aufgaben filtern,
beide Reports mit report.py schreiben, mit compare.py
vergleichen und die Runs der Rollen-Variante auflisten.

python auswertung.py
"""
import json
import statistics
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
CODE = HIER.parents[1]
sys.path[:0] = [str(HIER.parent / "solution"),
                str(CODE / "kapitel10" / "solution")]

import report  # Kapitel 10
from compare import compare, load

MULTI = HIER / "ergebnisse_multi" / "results.jsonl"
BASIS = CODE / "kapitel10/messung/ergebnisse/results.jsonl"


def lines(p: Path) -> list[dict]:
    return [json.loads(z) for z in
            p.read_text(encoding="utf-8").splitlines() if z]


def main() -> None:
    multi = lines(MULTI)
    ids = {r["task"] for r in multi}
    basis = [r for r in lines(BASIS) if r["task"] in ids]
    sub = HIER / "baseline_gleiche_aufgaben"
    sub.mkdir(exist_ok=True)
    (sub / "results.jsonl").write_text("".join(
        json.dumps(r, ensure_ascii=False) + "\n"
        for r in basis), encoding="utf-8")
    report.main(sub / "results.jsonl")
    report.main(MULTI)
    a = load(sub / "report.json", mixed_ok=True)
    b = load(MULTI.parent / "report.json")
    print("A = Baseline Kap. 10, B = Planner/Coder/Reviewer")
    print("\n".join(compare(a, b)))
    print()
    for name, rs in (("Baseline", basis), ("Rollen", multi)):
        tok = [r["input_tokens"] + r["output_tokens"] for r in rs]
        sec = [r["seconds"] for r in rs]
        print(f"{name}: Runs {len(rs)}, Token Median "
              f"{statistics.median(tok)}, min {min(tok)}, max "
              f"{max(tok)}; Sekunden Summe {sum(sec)}, Median "
              f"{statistics.median(sec)}, max {max(sec)}")
    print()
    for r in multi:
        rollen = {k: v["tokens"] for k, v in
                  r.get("roles", {}).items() if v["tokens"]}
        print(r["task"], r["run"], r["outcome"],
              "approved" if r["approved"] else "-",
              f"{r['seconds']} s", r.get("tool_calls"),
              (r.get("abort") or "")[:70])
        print("   ", rollen, "reviews", r.get("reviews"),
              "tester", [(t["green"], sorted(t["changed"]))
                         for t in r.get("tester", [])],
              "f2p", r["fail_to_pass"], "p2p", r["pass_to_pass"])


if __name__ == "__main__":
    main()
