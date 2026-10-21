"""Tests für Anhang F: pytest-Beispiele und Skript-Lauf."""

import subprocess
import sys
from pathlib import Path

import pytest

import versand
from versand import shipping_cost


def test_genau_50_euro_ist_versandfrei():
    assert shipping_cost(50.0) == 0.0
    assert shipping_cost(49.99) == 4.95


def test_unbekanntes_land():
    with pytest.raises(ValueError, match="kein Versand"):
        shipping_cost(10.0, country="FR")


@pytest.fixture
def ticket(tmp_path):
    path = tmp_path / "NL-101.md"
    path.write_text("ab 50 EUR frei", encoding="utf-8")
    return path


def test_ticket_lesen(ticket):
    assert "50 EUR" in ticket.read_text(encoding="utf-8")


def test_grenze_ersetzen(monkeypatch):
    monkeypatch.setattr(versand, "FREE_SHIPPING_FROM", 100.0)
    assert shipping_cost(60.0) == 4.95


HERE = Path(__file__).parent


@pytest.mark.parametrize(
    "script", sorted(HERE.glob("f[0-9]*.py")), ids=str)
def test_beispiel_laeuft(script):
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", script.name, "50"],
        cwd=HERE, capture_output=True, check=False)
    assert proc.returncode == 0, proc.stderr
