"""python eval_gate.py evals/baseline.json report.json

Blockierendes Eval-Gate für die CI. Liest die Baseline-
Datei mit Schwellen und den Report des aktuellen Runs
(Schema v1, Kapitel 10). Exit 0: grün, 1: rot,
2: Reports lassen sich nicht vergleichen."""
import json
import sys
from pathlib import Path

from regression_alert import alerts, load  # Kapitel 13


def mixed(rep: dict) -> list[str]:
    """Mehr als ein Modell, Prompt oder Harness im Report."""
    return [f"{k}: {', '.join(v)}"
            for k, v in rep["versions"].items() if len(v) > 1]


def limits(cur: dict, lim: dict) -> list[str]:
    """Absolute Schwellen, unabhängig von der Baseline."""
    out = [f"{f} {cur[f]} > {lim[f]} (absolut)"
           for f in ("policy", "tests_changed", "over_budget")
           if f in lim and cur[f] > lim[f]]
    if "cost_mean" in lim and cur["cost"] and (
            cur["cost"]["mean"] > lim["cost_mean"]):
        out.append(f"Kosten je Run {cur['cost']['mean']:.4f}"
                   f" > {lim['cost_mean']} (absolut)")
    return out


def gate(cfg_path: Path, cur_path: Path) -> int:
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    base = load(cfg_path.parent / cfg["report"])
    cur = load(cur_path)
    if found := mixed(cur):
        print("Gemischte Konfiguration:", *found, sep="\n  ")
        return 2
    if set(base["tasks"]) != set(cur["tasks"]):
        print("Verschiedene Aufgaben, kein Vergleich möglich.")
        return 2
    o = cur["overall"]
    found = (alerts(base["overall"], o, cfg["relative"])
             + limits(o, cfg.get("absolute", {})))
    for f in found:
        print("ROT:", f)
    farbe = "rot" if found else "grün"
    print(f"Eval-Gate {farbe}: {o['resolved']}/{o['runs']}"
          f" gelöst, {len(found)} Befund(e)")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(gate(Path(sys.argv[1]), Path(sys.argv[2])))
