from pathlib import Path

import yaml

WF = Path(__file__).parent / ".github/workflows/snapshot-check.yml"


def test_monatlich_mit_issue_bei_rot():
    wf = yaml.safe_load(WF.read_text(encoding="utf-8"))
    trigger = wf[True]                 # YAML liest "on" als True
    assert set(trigger) == {"schedule", "workflow_dispatch"}
    assert wf["permissions"] == {"contents": "read"}
    steps = wf["jobs"]["pruefen"]["steps"]
    assert steps[-1]["if"] == "failure()"
    assert "gh issue create" in steps[-1]["run"]
