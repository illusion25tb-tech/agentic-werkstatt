"""Git-Netz und Prozessbaum: die beiden harten Grenzen."""
import sys
import time

import pytest

import git_ops
from tools_exec import run_capped

V = "bestellservice/versand.py"

ENKEL = (
    "import subprocess, sys, time\n"
    "subprocess.Popen([sys.executable, '-c', 'import time;"
    " time.sleep(4); open(\"marker\", \"w\").close()'])\n"
    "time.sleep(60)\n")


def test_schmutziger_baum_bricht_vor_dem_run_ab(repo):
    (repo / V).write_text("kaputt")
    with pytest.raises(git_ops.DirtyTree):
        git_ops.start(repo, "NL-107")


def test_verwerfen_stellt_ausgangszustand_her(repo):
    vorher = (repo / V).read_bytes()
    base = git_ops.start(repo, "NL-107")
    (repo / V).write_text("geändert")
    (repo / "neu.py").write_text("x = 1\n")
    git_ops.discard(repo, base, "NL-107")
    assert (repo / V).read_bytes() == vorher
    assert not (repo / "neu.py").exists()
    assert git_ops.git(repo, "branch") == "* main\n"


def test_timeout_raeumt_den_prozessbaum_ab(tmp_path):
    t0 = time.monotonic()
    code, out = run_capped([sys.executable, "-c", ENKEL],
                           tmp_path, timeout=2)
    assert code is None and "Zeitlimit" in out
    assert time.monotonic() - t0 < 10
    time.sleep(4)                   # Enkel hätte jetzt
    assert not (tmp_path / "marker").exists()   # geschrieben
