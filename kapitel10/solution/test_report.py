"""Report aus synthetischen Ergebnissen, Snapshot-Vergleich."""
import json
from pathlib import Path

import report

SNAP = Path(__file__).parent / "fixtures/report_expected.md"


def rec(task, run, ok, outcome, cost, calls, asked=1,
        changed=()):
    return {"task": task, "run": run, "resolved": ok,
            "outcome": outcome, "cost": cost,
            "tool_calls": calls, "asked": asked, "policy": 0,
            "tests_changed": list(changed),
            "over_budget": cost > 0.5, "model": "m",
            "prompt": "p1", "harness": "h1"}


RECS = [
    rec("NL-111", 1, True, "gelöst", 0.10, 9),
    rec("NL-111", 2, True, "gelöst", 0.12, 11),
    rec("NL-111", 3, True, "gelöst", 0.11, 10),
    rec("NL-112", 1, True, "gelöst", 0.20, 14),
    rec("NL-112", 2, False, "falsch", 0.25, 18),
    rec("NL-112", 3, False, "budget", 0.60, 30,
        changed=["tests/test_x.py"]),
    rec("NL-113", 1, False, "übergabe", 0.30, 22, 0),
    rec("NL-113", 2, False, "budget", 0.55, 30),
    rec("NL-113", 3, False, "falsch", 0.20, 16)]


def test_report(tmp_path):
    res = tmp_path / "results.jsonl"
    res.write_text("\n".join(json.dumps(r) for r in RECS),
                   encoding="utf-8")
    rep = report.main(res)
    o = rep["overall"]
    assert (o["resolved"], o["runs"]) == (4, 9)
    assert o["ci95"] == [0.1888, 0.7334]
    assert rep["tasks"]["NL-112"]["status"] == "wackelnd"
    assert o["tests_changed"] == 1 and o["over_budget"] == 2
    md = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert md == SNAP.read_text(encoding="utf-8")
    assert json.loads((tmp_path / "report.json").read_text(
        encoding="utf-8"))["version"] == 1


def test_preis_fehlt():
    r = [rec("NL-111", 1, True, "gelöst", 0.1, 9)]
    r[0]["cost"] = None
    assert report.summarize(r)["overall"]["cost"] is None
