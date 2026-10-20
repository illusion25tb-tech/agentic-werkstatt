"""Rechenbeispiele des Kapitels und die Ablation aus
Kapitel 8, statistisch eingeordnet. Ohne Modell."""
import json
import sys
from collections import defaultdict
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent / "solution"))

from stats import pass_at_k, pass_hat_k, wilson


def ci(s: int, n: int) -> str:
    lo, hi = wilson(s, n)
    return f"{s}/{n} = {s / n:.0%}, 95 %: {lo:.1%} bis {hi:.1%}"


print("Einstieg:", ci(2, 3))
for s, n in [(1, 3), (15, 30), (18, 30), (21, 30), (50, 100),
             (60, 100), (150, 300), (0, 9), (0, 30)]:
    print(ci(s, n))

ABL = HIER.parents[1] / "kapitel08/messung/ergebnisse.jsonl"
rows = [json.loads(z) for z in ABL.read_text(
    encoding="utf-8").splitlines()]
print(f"\nKapitel 8: {len(rows)} Runs, Modell(e)",
      {r["model"] for r in rows}, {r["date"] for r in rows})
zelle = defaultdict(list)
for r in rows:
    zelle[r["bed"]].append(r)
for bed in ("ohne", "relevant", "rauschen", "vergiftet"):
    rs = zelle[bed]
    t = sum(r["trifft"] for r in rs)
    a = sum(r["angenommen"] for r in rs)
    print(f"{bed:10} trifft {ci(t, len(rs))} | "
          f"angenommen {ci(a, len(rs))}")
    for frage in ("F1", "F6"):
        q = [r for r in rs if r["frage"] == frage]
        c = sum(r["trifft"] for r in q)
        ca = sum(r["angenommen"] for r in q)
        print(f"   {frage}: trifft {c}/{len(q)} "
              f"pass@3 {pass_at_k(len(q), c, 3):.2f} "
              f"pass^3 {pass_hat_k(len(q), c, 3):.2f}; "
              f"angenommen {ca}/{len(q)} "
              f"pass^3 {pass_hat_k(len(q), ca, 3):.2f}")
alle = sum(r["trifft"] for r in rows)
mit = sum(r["trifft"] for r in rows if r["bed"] != "ohne")
print("gesamt trifft", ci(alle, len(rows)),
      "| mit Memory", ci(mit, 18))
# Wären beide Treffer reiner Zufall, mit welcher Chance
# fielen beide in die sechs Runs ohne Memory?
from math import comb

print(f"beide Treffer in 'ohne': {comb(6, 2)}/{comb(24, 2)}"
      f" = {comb(6, 2) / comb(24, 2):.3f}")
