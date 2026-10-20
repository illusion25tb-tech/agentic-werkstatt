"""guard_paths mit Beispiel-Diffs: erlaubt und verboten."""
import subprocess
import sys

from guard_paths import violations

ERLAUBT = ["M\tbestellservice/bestellservice/tariffs.py",
           "A\tbestellservice/tests/test_sperrgut.py"]
VERBOTEN = [
    "M\tkapitel14/solution/evals/baseline_report.json",
    "M\tbestellservice/tests/test_tariffs.py",
    "D\tbestellservice/tests/test_labels.py",
    "M\t.github/workflows/eval.yml",
    "A\tbestellservice/tests/conftest.py",
    "M\tbestellservice/pyproject.toml",
    "R087\ttests/test_a.py\ttests/test_b.py",
]


def test_code_und_neuer_test_sind_erlaubt():
    assert violations(ERLAUBT) == []


def test_jede_verbotene_zeile_wird_gemeldet():
    for zeile in VERBOTEN:
        assert violations([zeile]), zeile


def test_umbenennen_meldet_beide_pfade():
    assert violations([VERBOTEN[-1]]) == [
        "R tests/test_a.py: bestehender Test",
        "R tests/test_b.py: bestehender Test"]


def test_exit_code_ueber_stdin():
    diff = "\n".join(ERLAUBT + VERBOTEN[:1])
    r = subprocess.run([sys.executable, "guard_paths.py"],
                       input=diff, capture_output=True,
                       text=True, check=False)
    assert r.returncode == 1
    assert "baseline_report.json: geschützt" in r.stdout
