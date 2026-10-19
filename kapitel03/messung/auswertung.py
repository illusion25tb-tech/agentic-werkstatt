"""Wertet klassifizierer.jsonl aus (Break gegen Harden, je Modell)."""
import json
from collections import defaultdict
from pathlib import Path

recs = [json.loads(l) for l in (Path(__file__).parent / "klassifizierer.jsonl").open(encoding="utf-8")]
by = defaultdict(list)
for r in recs:
    by[(r["variante"], r["model"])].append(r)
for (v, model), rs in sorted(by.items()):
    inval = sum(not r["valid"] for r in rs)
    retry = sum(r["calls"] > 1 for r in rs)
    kat = defaultdict(dict)
    for r in rs:
        kat[r["issue"]][r["run"]] = r.get("kategorie") if r["valid"] else None
    both = [k for k, d in kat.items() if d.get(1) and d.get(2)]
    flip = sum(kat[k][1] != kat[k][2] for k in both)
    tin = sum(r["tokens_in"] for r in rs); tout = sum(r["tokens_out"] for r in rs)
    fehler = defaultdict(int)
    for r in rs:
        if not r["valid"]:
            fehler[str(r.get("fehler"))[:40]] += 1
    print(f"{v:6} {model:12} n={len(rs)} ungueltig={inval} retries={retry} "
          f"wechsel={flip}/{len(both)} tokens={tin}/{tout} fehler={dict(fehler)}")
