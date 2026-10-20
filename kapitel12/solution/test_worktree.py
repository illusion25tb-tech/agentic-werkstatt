from conftest import git
from worktree import worktree

V = "bestellservice/versand.py"


def test_zwei_coder_zwei_verzeichnisse(repo):
    with worktree(repo, "coder/a") as a, \
            worktree(repo, "coder/b") as b:
        (a / V).write_text("a = 1\n")
        git(a, "-c", "user.name=t", "-c", "user.email=t@t",
            "commit", "-qam", "a")
        assert "a = 1" not in (b / V).read_text()
        assert "a = 1" not in (repo / V).read_text()
    assert not a.exists() and not b.exists()
    assert git(repo, "worktree", "list").count("\n") == 1
    assert "a = 1" in git(repo, "show", f"coder/a:{V}")


def test_aufraeumen_auch_bei_fehler(repo):
    try:
        with worktree(repo, "coder/x") as x:
            (x / V).write_text("halb fertig\n")
            raise RuntimeError("Coder abgestürzt")
    except RuntimeError:
        pass
    assert not x.exists()
    assert git(repo, "status", "--porcelain") == ""
