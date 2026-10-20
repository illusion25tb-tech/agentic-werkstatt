import pytest
from pydantic import ValidationError

from roles import READ, ROLES, WRITE, Verdict


def test_verdict_ohne_beleg_ist_ungueltig():
    with pytest.raises(ValidationError):
        Verdict(approve=True, reason="sieht gut aus",
                evidence=[])


def test_nur_der_coder_schreibt():
    for name, role in ROLES.items():
        darf = set(role.tools) & set(WRITE)
        assert bool(darf) == (name == "coder"), name
        assert set(READ) <= set(role.tools)
