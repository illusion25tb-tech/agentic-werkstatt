from repo_map import repo_map
from tools import ROOT


def test_budget_wird_eingehalten():
    for budget in (600, 1500, 3000):
        assert len(repo_map(ROOT, budget)) <= budget


def test_tests_fallen_zuerst_weg():
    karte = repo_map(ROOT, 3000)
    assert "bestellservice/tracking.py | " in karte
    assert "README.md" in karte
    assert "tests/test_api.py" not in karte
    assert karte.splitlines()[-1].endswith(
        "Dateien ausgelassen (Budget)")


def test_ohne_kuerzung_alles_drin():
    karte = repo_map(ROOT, 100_000)
    assert "tests/test_api.py | test_health:4" in karte
    assert "ausgelassen" not in karte
    assert ("bestellservice/labels.py | LABEL_LINE_MAX:16"
            in karte)
