from pathlib import Path

import pytest

from capstone import release
from inject import inject, load

FAULTS = {f.id: f for f in load(
    Path(__file__).with_name("faults.yaml"))}


def test_ohne_stoerung_empfehlung(roles):
    assert release("NL-107", roles).result == "empfehlung"


@pytest.mark.parametrize("fid",
                         ["tool-timeout", "test-rot", "budget"])
def test_erkannt(roles, fid):
    out = release("NL-107", inject(roles, FAULTS[fid]))
    assert out.result == "eskalation"


@pytest.mark.parametrize("fid", ["leerer-diff", "abhaengigkeit"])
def test_luecke_im_starter(roles, fid):
    """Diese Störungen kommen bis zur Empfehlung durch."""
    out = release("NL-107", inject(roles, FAULTS[fid]))
    assert out.result == "empfehlung"
