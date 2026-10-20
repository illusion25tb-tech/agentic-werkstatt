from pathlib import Path

from diff_budget import Budget, check_diff, numstat

FIX = Path(__file__).parent / "fixtures"
SCOPE = Budget(["bestellservice/orders.py",
                "bestellservice/api.py",
                "bestellservice/models.py",
                "bestellservice/errors.py"],
               ["tests/test_acceptance_*.py"])


def lesen(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


def test_numstat_wie_git():
    # Werte aus git diff --numstat für dieselben Diffs
    ref = numstat(lesen("nl105_referenz.diff"))
    assert ref == {"bestellservice/api.py": [10, 0],
                   "bestellservice/errors.py": [4, 0],
                   "bestellservice/models.py": [4, 0],
                   "bestellservice/orders.py": [42, 0]}
    gross = numstat(lesen("nl105_riesen.diff"))
    assert len(gross) == 9
    assert gross["migrations/002_storno.sql"] == [10, 0]
    assert gross["tests/test_orders.py"] == [1, 1]


def test_kleiner_diff_passiert():
    assert check_diff(lesen("nl105_referenz.diff"), SCOPE) == []


def test_riesen_diff_wird_abgelehnt():
    fehler = check_diff(lesen("nl105_riesen.diff"), SCOPE)
    assert len(fehler) == 8
    assert "9 Dateien, erlaubt sind 5" in fehler
    assert fehler[-1].startswith("199 geänderte Zeilen")


def test_acceptance_test_ist_gesperrt():
    diff = ("--- a/tests/test_acceptance_nl105.py\n"
            "+++ b/tests/test_acceptance_nl105.py\n"
            "@@ -2 +2 @@\n"
            "-import pytest\n"
            "+import pytest  # xfail entfernt\n")
    assert check_diff(diff, SCOPE) == [(
        "tests/test_acceptance_nl105.py ist gesperrt "
        "(Acceptance Test)")]


def test_neue_datei_und_kein_diff():
    neu = "--- /dev/null\n+++ b/x.py\n@@ -0,0 +1 @@\n+a = 1\n"
    assert numstat(neu) == {"x.py": [1, 0]}
    assert "Kein Unified Diff" in check_diff("Hier ist der "
                                             "Code.", SCOPE)[0]


def test_diff_ohne_aenderung():
    # Gestalt aus einem echten Run (messung/traces/spec_1.diff)
    leer = ("--- a/bestellservice/api.py\n"
            "+++ b/bestellservice/api.py\n"
            "@@ -37,6 +37,8 @@\n"
            "     return inventory.stock_info(\n")
    assert check_diff(leer, SCOPE) == [
        "Der Diff ändert keine Zeile."]
