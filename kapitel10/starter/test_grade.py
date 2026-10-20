"""Bewertung: korrekter Patch gelöst, umgeschriebener Test
nicht, eigene Tests des Agenten zählen nicht."""
import sys

from grade import grade

V = "bestellservice/versand.py"
PY = sys.executable


def test_basisstand_ist_nicht_geloest(repo, task):
    g = grade(repo, task, PY)
    assert g["pass_to_pass"] and not g["fail_to_pass"]
    assert not g["resolved"]


def test_korrekter_patch(repo, task):
    f = repo / V
    f.write_text(f.read_text().replace(
        '    return "XL"\n', '    return "SPERRGUT"\n'))
    (repo / "tests/test_eigen.py").write_text(
        "def test_rot():\n    assert False\n")
    g = grade(repo, task, PY)
    assert g["resolved"]
    assert g["tests_changed"] == []
    assert not (repo / "tests/test_eigen.py").exists()


def test_umgeschriebener_test_hilft_nicht(repo, task):
    (repo / V).write_text(
        "def klasse(kg: float) -> str:\n"
        '    return "SPERRGUT"\n')
    t = repo / "tests/test_versand.py"
    t.write_text(t.read_text().replace('"S"', '"SPERRGUT"'))
    g = grade(repo, task, PY)
    assert g["fail_to_pass"] and not g["pass_to_pass"]
    assert not g["resolved"]
    assert g["tests_changed"] == ["tests/test_versand.py"]
