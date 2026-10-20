"""Statische Regeln für die Workflows dieses Kapitels."""
import re
from pathlib import Path

import pytest
import yaml

FLOWS = sorted((Path(__file__).parent / ".github/workflows")
               .glob("*.yml"))
FEST = re.compile(r"@(v\d+\.\d+\.\d+|[0-9a-f]{40})$")
FREMD = re.compile(r"\$\{\{\s*github\.event\.(issue|"
                   r"pull_request|comment)\.")


def load(p: Path) -> dict:
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def steps(flow: dict):
    for job in flow["jobs"].values():
        yield from job.get("steps", [])


@pytest.mark.parametrize("p", FLOWS, ids=lambda p: p.name)
def test_regeln(p):
    flow, text = load(p), p.read_text(encoding="utf-8")
    assert "permissions" in flow            # Least Privilege
    assert "pull_request_target" not in text
    for s in steps(flow):
        if "uses" in s:                     # feste Version
            assert FEST.search(s["uses"]), s["uses"]
        assert not FREMD.search(s.get("run", "")), s
    for job in flow["jobs"].values():       # Secrets nur
        if "secrets." in str(job):          # mit Environment
            assert "environment" in job


def test_deploy_wartet_auf_freigabe():
    job = load(FLOWS[[p.name for p in FLOWS]
                     .index("deploy.yml")])["jobs"]["produktion"]
    assert job["environment"] == "produktion"
    assert job["permissions"]["id-token"] == "write"
