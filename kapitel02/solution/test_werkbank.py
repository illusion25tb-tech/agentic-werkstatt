import subprocess
import tomllib

import check_werkbank as cw


def test_python_zu_alt():
    assert "zu alt" in cw.check_python((3, 11, 9))
    assert cw.check_python((3, 15, 0)) is None


def test_programm_fehlt(monkeypatch):
    monkeypatch.setattr(cw.shutil, "which", lambda n: None)
    assert "uv nicht gefunden" in cw.check_program("uv")


def fake_git(code):
    def run(cmd, **kw):
        return subprocess.CompletedProcess(cmd, code)

    return run


def test_env_nicht_ignoriert(monkeypatch):
    monkeypatch.setattr(cw.subprocess, "run", fake_git(1))
    assert "NICHT ignoriert" in cw.check_ignored()


def test_kein_repository(monkeypatch):
    monkeypatch.setattr(cw.subprocess, "run", fake_git(128))
    assert "kein Git-Repository" in cw.check_ignored()


def test_echtes_repository(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    subprocess.run(["git", "init", "-q"], check=True)
    assert cw.check_ignored() is not None
    (tmp_path / ".gitignore").write_text(".env\n")
    assert cw.check_ignored() is None


def test_main_exit_code(monkeypatch, capsys):
    monkeypatch.setattr(cw.shutil, "which", lambda n: None)
    assert cw.main() == 1
    assert "FEHLT: uv" in capsys.readouterr().out


def test_pyproject_mindestversion():
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    assert data["project"]["requires-python"] == ">=3.12"


def test_main_alles_da(monkeypatch, capsys):
    monkeypatch.setattr(cw.shutil, "which", lambda n: "/bin/x")
    monkeypatch.setattr(cw.subprocess, "run", fake_git(0))
    assert cw.main() == 0
    assert "Werkbank bereit." in capsys.readouterr().out
