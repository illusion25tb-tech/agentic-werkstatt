"""compare.py mit zwei erfundenen Reports. Die Zahlen sind
Testdaten, keine Messung."""
import json

import pytest

from compare import compare, load


def report(outcomes: dict, cost=0.3, harness=("h1",)):
    tasks = {}
    for t, o in outcomes.items():
        c = o.count("gelöst")
        tasks[t] = {"runs": len(o), "resolved": c,
                    "outcomes": o, "pass_at_k": float(c > 0),
                    "pass_hat_k": float(c == len(o)),
                    "status": "-"}
    n = sum(len(o) for o in outcomes.values())
    return {"schema": "agentic-werkstatt/eval-report",
            "version": 1, "k": 3,
            "versions": {"model": ["m"], "prompt": ["p"],
                         "harness": list(harness)},
            "overall": {"runs": n,
                        "cost": {"mean": cost, "stdev": 0.1},
                        "tool_calls": {"mean": 9.0,
                                       "stdev": 2.0}},
            "tasks": tasks}


G, U = "gelöst", "übergabe"
A = report({"NL-1": [G, G, G], "NL-2": [U, U, U],
            "NL-3": [U, U, U]})
B = report({"NL-1": [G, G, G], "NL-2": [G, U, U],
            "NL-3": [U, U, U]}, cost=0.6)


def test_kosten_je_geloestem_issue():
    out = "\n".join(compare(A, B))
    assert "3/9" in out and "4/9" in out
    # A: 0,3 × 9 Runs / 3 gelöst = 0,9; B: 0,6 × 9 / 4 = 1,35
    assert "0.9" in out and "1.35" in out
    assert "überlappen: ja" in out


def test_abweichende_issues():
    out = compare(A, B)
    assert any(z.startswith("NL-2") for z in out)
    assert not any(z.startswith("NL-1 ") for z in out)


def test_nur_gemeinsame_aufgaben():
    gross = report({"NL-1": [G, G, G], "NL-2": [U, U, U],
                    "NL-4": [G, G, G]})
    out = "\n".join(compare(gross, B))
    assert "Gemeinsame Aufgaben: 2 (nur A: 1, nur B: 1)" in out
    assert "3/6" in out             # NL-4 zählt nicht mit
    assert "n. v." in out           # Kosten nicht teilbar


def test_gemischte_fassungen(tmp_path):
    p = tmp_path / "report.json"
    p.write_text(json.dumps(report({"NL-1": [U]},
                                   harness=("h1", "h2"))))
    with pytest.raises(ValueError, match="gemischte"):
        load(p)
    assert load(p, mixed_ok=True)["k"] == 3
