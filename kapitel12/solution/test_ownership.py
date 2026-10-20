from conftest import git
from ownership import changed_files, foreign

V = "bestellservice/versand.py"


def test_fremde_datei_ist_ein_verstoss(repo):
    (repo / V).write_text("x = 1\n")
    (repo / "bestellservice/labels.py").write_text("y = 2\n")
    (repo / "tests/test_neu.py").write_text("")
    c = changed_files(repo)
    assert c == {V: "M", "bestellservice/labels.py": "M",
                 "tests/test_neu.py": "A"}
    assert foreign(c, [V]) == ["bestellservice/labels.py"]


def test_bestehender_test_gehoert_niemandem(repo):
    (repo / "tests/test_versand.py").write_text("")
    git(repo, "add", "-N", ".")
    assert foreign(changed_files(repo), [V]) == [
        "tests/test_versand.py"]


def test_windows_pfad_im_plan(repo):
    (repo / V).write_text("x = 1\n")
    assert foreign(changed_files(repo),
                   ["bestellservice\\versand.py"]) == []
