"""Fixture-Ergebnisse: Testdaten, keine Messung."""
from dashboard import board, p95


def rec(resolved, seconds, cost=0.1, outcome="gelöst"):
    return {"resolved": resolved, "seconds": seconds,
            "cost": cost, "tool_calls": 10, "errors": 1,
            "policy": 0, "outcome": outcome}


def test_kosten_je_geloestem_issue():
    b = board([rec(True, 10), rec(False, 20, outcome="budget")])
    assert b["Kosten je gelöstem Issue"] == 0.2
    assert b["Erfolgsquote"] == "1/2"
    assert b["Budget/Policy"] == (1, 0)


def test_null_geloest_ist_keine_zahl():
    b = board([rec(False, 10)])
    assert b["Kosten je gelöstem Issue"] == "n. v."


def test_p95_ist_nicht_der_mittelwert():
    xs = [10] * 19 + [1000]
    assert p95(xs) > 10 and p95(xs) < 1000
