from pathlib import Path

import pytest
from pydantic import ValidationError

from plan import Plan, check_plan, order

ROOT = (Path(__file__).parents[2] / "bestellservice").resolve()


def plan(**aenderung) -> Plan:
    s1 = {"id": "s1", "goal": "Status cancelled",
          "files": ["bestellservice/orders.py"],
          "check": "pytest tests/test_orders.py"}
    s2 = {"id": "s2", "goal": "Route",
          "files": ["bestellservice/api.py"],
          "check": "pytest tests", "depends_on": ["s1"]}
    s1.update(aenderung)
    return Plan(goal="NL-105", steps=[s2, s1])


def test_gueltiger_plan_passiert():
    p = plan()
    assert check_plan(p, ROOT) == []
    assert [s.id for s in order(p)] == ["s1", "s2"]


def test_fehlende_datei_und_check():
    fehler = check_plan(plan(files=["bestellservice/porto.py"],
                             check="sieht gut aus"), ROOT)
    assert fehler[0] == ("s1: bestellservice/porto.py "
                         "gibt es nicht")
    assert "kein Befehl" in fehler[1]


def test_pfad_ausserhalb_des_repos():
    fehler = check_plan(plan(files=["../issues/NL-105.md"]),
                        ROOT)
    assert "gibt es nicht" in fehler[0]


def test_zyklus_und_unbekannte_abhaengigkeit():
    assert "Zyklus" in check_plan(plan(depends_on=["s2"]),
                                  ROOT)[0]
    assert "'s9'" in check_plan(plan(depends_on=["s9"]),
                                ROOT)[0]


def test_schritt_ohne_check_und_dateien():
    with pytest.raises(ValidationError):
        plan(files=[])
    with pytest.raises(ValidationError):
        Plan(goal="x", steps=[{"id": "s1", "goal": "y",
                               "files": ["a.py"]}])
