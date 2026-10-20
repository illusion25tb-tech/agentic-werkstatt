from pathlib import Path

import pytest

from plan import Plan
from plan_execute import PlanFailed, applies, execute
from tools import ROOT

FIX = Path(__file__).parent / "fixtures"
REF = (FIX / "nl105_referenz.diff").read_text(encoding="utf-8")
BIG = (FIX / "nl105_riesen.diff").read_text(encoding="utf-8")
VIER = ["bestellservice/orders.py", "bestellservice/api.py",
        "bestellservice/models.py", "bestellservice/errors.py"]


def plan(sid: str, files: list[str]) -> Plan:
    return Plan(goal="NL-105", steps=[{
        "id": sid, "goal": "Storno", "files": files,
        "check": "pytest tests"}])


def test_git_apply_prueft_ohne_zu_schreiben():
    assert applies(REF, ROOT) == []
    assert "No valid patches" in applies("Hier ist der Code.",
                                         ROOT)[0]


def test_zweimal_abgelehnt_loest_neuplanung_aus():
    vorschlaege = iter([BIG, "Hier ist der Code.", REF])
    gesehen, neu = [], []

    def propose(step, fehler):
        gesehen.append((step.id, list(fehler)))
        return next(vorschlaege)

    def replan(p, step, fehler):
        neu.append(fehler)
        return plan("s1b", VIER)
    done = execute(plan("s1", VIER[:1]), propose, replan, ROOT)
    assert list(done) == ["s1b"] and done["s1b"] == REF
    assert len(neu) == 1
    assert "liegt außerhalb des Scopes" in gesehen[1][1][0]
    assert gesehen[2] == ("s1b", [])


def test_widerspruch_plant_sofort_neu():
    aufrufe = []

    def replan(p, step, fehler):
        aufrufe.append(fehler)
        return plan("s2", VIER)
    done = execute(plan("s1", ["bestellservice/porto.py"]),
                   lambda s, f: REF, replan, ROOT)
    assert aufrufe == [[("s1: bestellservice/porto.py gibt "
                         "es nicht")]]
    assert list(done) == ["s2"]


def test_zweite_neuplanung_bricht_ab():
    with pytest.raises(PlanFailed, match="s1b"):
        execute(plan("s1", VIER), lambda s, f: BIG,
                lambda p, s, f: plan("s1b", VIER), ROOT)
