"""python report.py Name=pfad/results.jsonl ...

Ergebnistabelle für den Capstone-Report: je Variante Erfolg
mit 95-%-Intervall, dazu Median oder Mittel und Spannweite.
Liest results.jsonl aus Kapitel 10 und 12."""
import json
import sys
from collections import Counter
from pathlib import Path
from statistics import mean, median

KAP10 = Path(__file__).resolve().parents[2] / "kapitel10"
sys.path.append(str(KAP10 / "solution"))

from stats import wilson  # Kapitel 10

HEAD = ("| Variante | Runs | gelöst (95 %) | Tool Calls Ø "
        "| Token Median | Sekunden Median | Policy "
        "| Reviews |\n"
        "|---|---|---|---|---|---|---|---|")


def span(xs: list, avg=median) -> str:
    """Median (oder Mittelwert) und Spannweite."""
    return f"{round(avg(xs), 1):g} ({min(xs)}–{max(xs)})"


def row(name: str, rs: list[dict]) -> str:
    n, c = len(rs), sum(r["resolved"] for r in rs)
    lo, hi = wilson(c, n)
    tok = [r["input_tokens"] + r["output_tokens"] for r in rs]
    rev = (sum(len(r["reviews"]) for r in rs)
           if all("reviews" in r for r in rs) else "–")
    cells = [name, n, f"{c}/{n} ({lo:.0%}–{hi:.0%})",
             span([r["tool_calls"] for r in rs], mean),
             span(tok), span([r["seconds"] for r in rs]),
             sum(r["policy"] for r in rs), rev]
    return "| " + " | ".join(map(str, cells)) + " |"


def setup(name: str, rs: list[dict]) -> str:
    v = {k: sorted({r[k] for r in rs})
         for k in ("model", "prompt", "harness")}
    ends = Counter(r["outcome"] for r in rs)
    return (f"- {name}: " + "; ".join(
        f"{k} {', '.join(x)}" for k, x in v.items())
        + "; Ausgänge " + ", ".join(
            f"{k} {n}" for k, n in sorted(ends.items())))


def report(variants: dict[str, list[dict]]) -> str:
    rows = [row(k, rs) for k, rs in variants.items()]
    notes = [setup(k, rs) for k, rs in variants.items()]
    return "\n".join([HEAD, *rows, "", *notes]) + "\n"


def load(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(z) for z in f if z.strip()]


if __name__ == "__main__":
    pairs = (a.split("=", 1) for a in sys.argv[1:])
    sys.stdout.reconfigure(encoding="utf-8")
    print(report({k: load(Path(p)) for k, p in pairs}), end="")
