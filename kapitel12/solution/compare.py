"""python compare.py A/report.json B/report.json [--gemischt]

Zwei Eval-Reports aus Kapitel 10 (Schema v1) auf den
Aufgaben, die beide enthalten: Erfolg mit Intervall, Kosten
je gelöstem Issue, Streuung, Issues mit anderem Ausgang."""
import json
import sys
from pathlib import Path
from statistics import mean

KAP10 = Path(__file__).resolve().parents[2] / "kapitel10"
sys.path.insert(0, str(KAP10 / "solution"))

from stats import wilson  # Kapitel 10

SCHEMA = ("agentic-werkstatt/eval-report", 1)


def load(path: Path, mixed_ok: bool = False) -> dict:
    rep = json.loads(path.read_text(encoding="utf-8"))
    if (rep.get("schema"), rep.get("version")) != SCHEMA:
        raise ValueError(f"{path}: kein Report im Schema v1")
    mixed = [f for f, v in rep["versions"].items()
             if len(v) > 1]
    if mixed and not mixed_ok:     # Kapitel 10: ein Fehler
        raise ValueError(f"{path}: gemischte Fassungen bei "
                         f"{mixed}; bewusst mit --gemischt")
    return rep


def side(rep: dict, ids: list[str]) -> dict:
    """Kennzahlen einer Variante, nur auf den Aufgaben ids."""
    t = [rep["tasks"][i] for i in ids]
    n = sum(x["runs"] for x in t)
    c = sum(x["resolved"] for x in t)
    o, alle = rep["overall"], set(ids) == set(rep["tasks"])
    s = {"n": n, "c": c, "ci": wilson(c, n), "k": rep["k"],
         "hat": mean(x["pass_hat_k"] for x in t),
         "cost": o["cost"] if alle else None,
         "calls": o["tool_calls"] if alle else None,
         "per_solved": None}
    if s["cost"] is not None and c:     # 0 gelöst: keine Zahl
        s["per_solved"] = s["cost"]["mean"] * o["runs"] / c
    return s


def _ms(x: dict | None) -> str:
    if x is None:
        return "n. v."
    return f"{x['mean']:.4g} ± {x['stdev']:.4g}"


def compare(a: dict, b: dict) -> list[str]:
    ids = sorted(set(a["tasks"]) & set(b["tasks"]))
    if not ids:
        raise ValueError("Keine gemeinsamen Aufgaben")
    sa, sb = side(a, ids), side(b, ids)
    out = [(f"Gemeinsame Aufgaben: {len(ids)} (nur A: "
            f"{len(set(a['tasks']) - set(ids))}, nur B: "
            f"{len(set(b['tasks']) - set(ids))})"),
           f"{'':18}{'A':>21}{'B':>21}"]

    def row(name, f):
        out.append(f"{name:18}{f(sa):>21}{f(sb):>21}")
    row("gelöst", lambda s: f"{s['c']}/{s['n']}")
    row("95-%-Intervall", lambda s: (
        f"{s['ci'][0]:.0%} bis {s['ci'][1]:.0%}"))
    row("pass^k", lambda s: f"{s['hat']:.2f} (k={s['k']})")
    row("Kosten je Run", lambda s: _ms(s["cost"]))
    row("je gelöstem Issue", lambda s: "n. v."
        if s["per_solved"] is None
        else f"{s['per_solved']:.4g}")
    row("Tool Calls je Run", lambda s: _ms(s["calls"]))
    lo = max(sa["ci"][0], sb["ci"][0])
    hi = min(sa["ci"][1], sb["ci"][1])
    out.append("Intervalle überlappen: " + (
        "ja, Unterschied nicht belastbar" if lo <= hi
        else "nein"))
    for i in ids:
        oa = a["tasks"][i]["outcomes"]
        ob = b["tasks"][i]["outcomes"]
        if sorted(oa) != sorted(ob):
            out.append(f"{i}  A: {', '.join(oa)}")
            out.append(f"{'':8}B: {', '.join(ob)}")
    return out


if __name__ == "__main__":
    args = [x for x in sys.argv[1:] if x != "--gemischt"]
    ok = "--gemischt" in sys.argv
    reps = [load(Path(p), ok) for p in args]
    print("\n".join(compare(*reps)))
