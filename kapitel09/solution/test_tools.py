"""Lesen, Schreiben, Testen: ohne Modell, ohne Framework."""
import pytest

import git_ops
from tools_exec import HandOver, run_tests
from tools_read import list_files, read_file, search
from tools_write import create_test, replace_in_file

V = "bestellservice/versand.py"


def test_lesen_mit_zeilen_und_grenze(deps):
    assert "tests/test_versand.py" in list_files(deps)
    assert "   8|     return \"XL\"" in read_file(deps,
                                                  V)
    assert "versand.py:8:" in search(deps, 'return "XL"')
    with pytest.raises(PermissionError):
        read_file(deps, "../geheim.txt")


@pytest.mark.parametrize("old", ["", "kg", "gibt es nicht"])
def test_old_muss_genau_einmal_vorkommen(deps, old):
    with pytest.raises(ValueError, match="genau einmal"):
        replace_in_file(deps, V, old, "x")


def test_budget_nimmt_aenderung_zurueck(deps):
    vorher = (deps.repo / V).read_bytes()
    with pytest.raises(ValueError, match="Zurückgenommen"):
        replace_in_file(deps, V, 'return "XL"\n',
                        'return "XL"\n' + "# x\n" * 30)
    assert (deps.repo / V).read_bytes() == vorher


def test_acceptance_test_ist_gesperrt(deps):
    with pytest.raises(ValueError, match="gesperrt"):
        replace_in_file(deps, "tests/test_acceptance_x.py",
                        '"SPERRGUT"', '"XL"')


def test_create_test_nur_neu(deps):
    with pytest.raises(FileExistsError):
        create_test(deps, "tests/test_versand.py", "")
    create_test(deps, "tests/test_neu.py", "def test_a():\n"
                "    assert True\n")
    assert "tests/test_neu.py" in git_ops.diff(deps.repo)


def test_rot_gruen_und_uebergabe(deps):
    assert "pytest ROT" in run_tests(deps)
    assert not deps.last_green
    replace_in_file(deps, V, '    return "XL"\n',
                    '    return "SPERRGUT"\n')
    assert "pytest grün" in run_tests(deps)
    assert deps.last_green and deps.red_streak == 0
    deps.red_streak = 2
    with pytest.raises(HandOver):
        run_tests(deps, "tests/fehlt.py")


def test_target_nur_unter_tests(deps):
    with pytest.raises(ValueError, match="unter tests/"):
        run_tests(deps, V)
