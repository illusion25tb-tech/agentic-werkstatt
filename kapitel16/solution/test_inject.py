from pathlib import Path

import pytest
from pydantic import ValidationError

from capstone import new_deps, release
from inject import Fault, inject, load

FAULTS = load(Path(__file__).with_name("faults.yaml"))


def test_ohne_stoerung_empfehlung(roles):
    out = release("NL-107", roles)
    assert out.result == "empfehlung"
    assert out.trail[-1] == "release_reviewer"


@pytest.mark.parametrize("f", FAULTS, ids=lambda f: f.id)
def test_jede_stoerung_eskaliert(roles, f):
    out = release("NL-107", inject(roles, f))
    assert out.result == "eskalation", out.reason
    assert "release_reviewer" not in out.trail


def test_fuenf_faelle_im_schema():
    assert [f.id for f in FAULTS] == [
        "tool-timeout", "test-rot", "leerer-diff",
        "abhaengigkeit", "budget"]


def test_unbekannter_effekt_scheitert_am_schema():
    with pytest.raises(ValidationError):
        Fault(id="x", role="tester", effect="langsam")


def test_budget_aus_kapitel_13(roles):
    f = Fault(id="b", role="planner", effect="budget")
    out = release("NL-107", inject(roles, f))
    assert out.reason.startswith("BudgetExceeded")
    assert out.trail == []


def test_bekannte_abhaengigkeit_ist_kein_befund():
    diff = ("--- a/pyproject.toml\n+++ b/pyproject.toml\n"
            '+    "pydantic>=2",\n+    "requestz==2.32.0",\n')
    assert new_deps(diff) == ["requestz"]


def test_geaenderter_test_ist_befund(roles):
    roles["implementer"] = lambda plan: (
        "--- a/tests/test_tariffs.py\n"
        "+++ b/tests/test_tariffs.py\n-x\n+y\n")
    out = release("NL-107", roles)
    assert out.reason == "Test geändert: tests/test_tariffs.py"


def test_ohne_security_reviewer_kommt_abhaengigkeit_durch(
        roles):
    roles["security"] = lambda d: []   # Break: Rolle entfernt
    f = next(f for f in FAULTS if f.id == "abhaengigkeit")
    assert release("NL-107", inject(roles, f)).result == (
        "empfehlung")
