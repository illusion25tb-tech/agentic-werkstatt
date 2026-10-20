"""AGENTS.md darf nichts versprechen, was es nicht gibt."""
import re
import tomllib
from pathlib import Path

from tools import ROOT

TEXT = (Path(__file__).parent / "AGENTS.md").read_text(
    encoding="utf-8")
BEFEHLE = TEXT.split("## Befehle")[1].split("##")[0]


def test_jeder_befehl_ist_eine_dev_abhaengigkeit():
    pp = tomllib.loads((ROOT / "pyproject.toml").read_text(
        encoding="utf-8"))
    dev = " ".join(pp["dependency-groups"]["dev"])
    for cmd in re.findall(r"`([^`]+)`", BEFEHLE):
        tool = cmd.removeprefix("python -m ").split()[0]
        assert tool in dev, f"{tool} fehlt in pyproject.toml"


def test_jeder_genannte_pfad_existiert():
    pfade = re.findall(r"`([\w/]+(?:\.py)?/?)`", TEXT)
    pfade = [p for p in pfade if "/" in p]
    assert "bestellservice/labels.py" in pfade
    for p in pfade:
        assert (ROOT / p).exists(), p
