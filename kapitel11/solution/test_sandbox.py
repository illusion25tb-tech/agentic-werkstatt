import json
from itertools import pairwise
from pathlib import Path

import pytest

import sandbox


def test_argumentliste_ohne_docker(tmp_path):
    repo, work = tmp_path / "repo", tmp_path / "work"
    a = sandbox.docker_args(repo, work, ["pytest", "-q"],
                            {"LANG": "C.UTF-8"}, "agent-x")
    flag = dict(pairwise(a))
    assert flag["--network"] == "none"
    assert flag["--cap-drop"] == "ALL"
    assert flag["--user"] == "1000:1000"
    assert flag["--security-opt"] == "no-new-privileges=true"
    assert "--read-only" in a
    assert f"type=bind,src={repo},dst=/repo,readonly" in a
    assert f"type=bind,src={work},dst=/work" in a
    assert a[a.index("--env") + 1] == "LANG=C.UTF-8"
    assert a.count("--env") == 1        # nichts geerbt
    assert a[-3:] == [sandbox.IMAGE, "pytest", "-q"]


NETZ = ("import urllib.request as u; "
        "u.urlopen('https://pypi.org', timeout=5)")


@pytest.mark.skipif(not sandbox.docker_ready(),
                    reason="Docker läuft nicht")
def test_im_container_kein_netz_kein_schreiben(tmp_path):
    repo, work = tmp_path / "repo", tmp_path / "work"
    repo.mkdir()
    work.mkdir()
    cmd = ["python", "-c", NETZ]
    code, _ = sandbox.run(repo, work, cmd, {})
    assert code != 0                    # kein Netz
    code, _ = sandbox.run(repo, work, ["touch", "/repo/x"], {})
    assert code != 0                    # read-only
    assert not (repo / "x").exists()


def test_devcontainer_hat_dieselben_grenzen():
    cfg = json.loads(Path(".devcontainer/devcontainer.json")
                     .read_text("utf-8"))
    args = dict(pairwise(cfg["runArgs"]))
    assert args["--network"] == "none"
    assert args["--cap-drop"] == "ALL"
