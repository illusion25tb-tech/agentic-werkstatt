"""Fixture-Reports: Testdaten im Schema v1."""
import copy
import json

from regression_alert import alerts, main

BASE = {"schema": "agentic-werkstatt/eval-report", "version": 1,
        "tasks": {"NL-111": {}, "NL-112": {}},
        "overall": {"rate": 0.6, "ci95": [0.42, 0.75],
                    "policy": 0, "tests_changed": 0,
                    "over_budget": 1,
                    "cost": {"mean": 0.20, "stdev": 0.05},
                    "tool_calls": {"mean": 8.0, "stdev": 3.0}}}


def variant(**overall):
    rep = copy.deepcopy(BASE)
    rep["overall"].update(overall)
    return rep


def write(tmp_path, name, rep):
    p = tmp_path / name
    p.write_text(json.dumps(rep), encoding="utf-8")
    return str(p)


def test_innerhalb_der_schwellen(tmp_path):
    cur = variant(rate=0.5, ci95=[0.33, 0.67],
                  cost={"mean": 0.22, "stdev": 0.06})
    args = [write(tmp_path, "b", BASE),
            write(tmp_path, "c", cur)]
    assert main(args) == 0


def test_ausserhalb_der_schwellen(tmp_path):
    cur = variant(rate=0.2, ci95=[0.09, 0.38], policy=1,
                  cost={"mean": 0.31, "stdev": 0.1})
    args = [write(tmp_path, "b", BASE),
            write(tmp_path, "c", cur)]
    assert main(args) == 1
    found = alerts(BASE["overall"], cur["overall"])
    assert len(found) == 3


def test_preis_fehlt_ist_alarm():
    cur = variant(cost=None)["overall"]
    assert alerts(BASE["overall"], cur) == [
        "Kosten unbekannt (Preis fehlt)"]


def test_andere_aufgaben(tmp_path):
    cur = copy.deepcopy(BASE)
    cur["tasks"] = {"NL-111": {}}
    args = [write(tmp_path, "b", BASE),
            write(tmp_path, "c", cur)]
    assert main(args) == 2
