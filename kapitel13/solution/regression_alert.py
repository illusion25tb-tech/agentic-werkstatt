"""python regression_alert.py baseline/report.json report.json

Vergleicht einen Eval-Report (Schema v1, Kapitel 10) mit
einer gespeicherten Baseline. Exit-Code 1 bei Alarm, 2 bei
Reports, die sich nicht vergleichen lassen."""
import json
import sys
from pathlib import Path

SCHEMA = ("agentic-werkstatt/eval-report", 1)
LIMITS = {               # Beispielwerte, je Team festzulegen
    "cost_rise": 0.25,       # Kosten je Run, relativ
    "calls_rise": 0.50,      # Tool Calls je Run, relativ
}


def load(path: Path) -> dict:
    rep = json.loads(path.read_text(encoding="utf-8"))
    if (rep.get("schema"), rep.get("version")) != SCHEMA:
        raise ValueError(f"{path}: kein Report im Schema v1")
    return rep


def rise(new: float, old: float) -> float:
    return (new - old) / old if old else float(new > 0)


def alerts(base: dict, cur: dict, lim=LIMITS) -> list[str]:
    """base, cur: Block 'overall' zweier Reports."""
    out = []
    if cur["ci95"][1] < base["rate"]:   # Intervall aus Kap. 10
        out.append(f"Erfolgsquote {base['rate']:.0%} -> "
                   f"{cur['rate']:.0%}, Baseline über "
                   "dem Intervall")
    for f in ("policy", "tests_changed", "over_budget"):
        if cur[f] > base[f]:        # Sicherheit: jede Zunahme
            out.append(f"{f} {base[f]} -> {cur[f]}")
    if base["cost"] and not cur["cost"]:
        out.append("Kosten unbekannt (Preis fehlt)")
    elif base["cost"]:
        old, new = base["cost"]["mean"], cur["cost"]["mean"]
        if rise(new, old) > lim["cost_rise"]:
            out.append(f"Kosten je Run {old:.4f} -> {new:.4f}")
    old = base["tool_calls"]["mean"]
    new = cur["tool_calls"]["mean"]
    if rise(new, old) > lim["calls_rise"]:
        out.append(f"Tool Calls je Run {old:.1f} -> {new:.1f}")
    return out


def main(args: list[str]) -> int:
    base, cur = (load(Path(p)) for p in args[:2])
    if set(base["tasks"]) != set(cur["tasks"]):
        print("Verschiedene Aufgaben, kein Vergleich möglich.")
        return 2
    found = alerts(base["overall"], cur["overall"])
    print("\n".join(found) or "Keine Regression gefunden.")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
