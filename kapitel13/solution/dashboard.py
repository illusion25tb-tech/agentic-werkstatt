"""python dashboard.py ergebnisse/results.jsonl

Die fünf Kennzahlen für den Morgen, aus den Ergebnissen
einer Eval-Suite (Kapitel 10 und 12). Dimensionen: nur
Agent und Rolle, keine Personen."""
import json
import sys
from collections import Counter
from pathlib import Path
from statistics import median, quantiles


def p95(xs: list[float]) -> float:
    if len(xs) < 2:
        return xs[0]
    return quantiles(xs, n=20, method="inclusive")[-1]


def board(recs: list[dict]) -> dict:
    n = len(recs)
    solved = sum(r["resolved"] for r in recs)
    cost = [r["cost"] for r in recs]
    sec = [r["seconds"] for r in recs]
    calls = sum(r["tool_calls"] for r in recs)
    roles = Counter()
    for r in recs:
        for name, v in r.get("roles", {}).items():
            roles[name] += v["tokens"]
    return {
        "Erfolgsquote": f"{solved}/{n}",
        "Kosten je gelöstem Issue": "n. v." if not solved
        or None in cost else round(sum(cost) / solved, 4),
        "Laufzeit p50/p95 (s)": (median(sec), round(p95(sec))),
        "Tool-Fehlerquote": f"{sum(r['errors'] for r in recs)}"
        f"/{calls}",
        "Budget/Policy": (sum(r["outcome"] == "budget"
                              for r in recs),
                          sum(r["policy"] for r in recs)),
        "Token je Rolle": dict(roles) or None,
    }


if __name__ == "__main__":
    p = Path(sys.argv[1])
    recs = [json.loads(z) for z in p.read_text(
        encoding="utf-8").splitlines() if z.strip()]
    for k, v in board(recs).items():
        print(f"{k:26}{v}")
