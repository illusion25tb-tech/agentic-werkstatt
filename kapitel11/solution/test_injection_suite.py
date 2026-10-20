"""Je Fall in adversarial/faelle.json: Das geskriptete Modell
befolgt die Injection, der Harness muss blockieren."""
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from deps import Deps
from diff_budget import Budget
from pydantic_ai.exceptions import UnexpectedModelBehavior

import http_tool
import secure_agent
from conftest import KEY, git, skript
from taint_policy import TaintPolicy

ADV = Path(__file__).parent / "adversarial"
FAELLE = json.loads((ADV / "faelle.json").read_text("utf-8"))


def schritte(fall) -> list:
    text = json.dumps(fall["schritte"]).replace("{KEY}", KEY)
    return [tuple(s) for s in json.loads(text)]


@pytest.mark.parametrize("fall", FAELLE, ids=lambda f: f["id"])
def test_harness_blockiert(fall, repo, tmp_path, monkeypatch):
    fremd = (ADV / fall["datei"]).read_text("utf-8")
    if fall["ziel"] == "http":          # Webseite, kein Netz
        monkeypatch.setattr(
            http_tool.urllib.request, "urlopen",
            lambda *a, **k: io.BytesIO(fremd.encode()))
    elif fall["ziel"]:
        shutil.copy(ADV / fall["datei"], repo / fall["ziel"])
        git(repo, "-c", "user.name=t", "-c", "user.email=t@t",
            "commit", "-qam", "präpariert")
    fragen, antworten = [], list(fall["antworten"])

    def approve(risk, tool, args):
        fragen.append(str(risk))
        return antworten.pop(0)
    pol = TaintPolicy(secrets=[KEY],
                      tainted_by=list(fall["start"]))
    deps = Deps(repo, pol,
                approve, Budget(["bestellservice/*.py",
                                 "tests/test_*.py"], []),
                tmp_path / "trace.jsonl", sys.executable)
    auftrag = fremd if fall["ziel"] is None else "NL-190"
    model = skript(*schritte(fall), "Fertig.")
    try:
        secure_agent.agent._run(secure_agent.SAFE_WORKER,
                                auftrag, deps, model, "butler")
    except UnexpectedModelBehavior:
        pass                            # Skript zu Ende
    trace = deps.trace.read_text("utf-8")
    for e in fall["erwartet"]:
        assert e in trace
    assert fragen == fall["fragen"]
    assert KEY not in trace             # auch nicht im Trace
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=repo,
        capture_output=True, text=True, check=True).stdout
    assert status == ""                 # nichts geschrieben
