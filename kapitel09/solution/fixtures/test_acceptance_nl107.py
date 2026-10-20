"""Acceptance Test NL-107, von Hand (Meilenstein 1).

Rot auf dem Basisstand: Bestellung 10262, Werkbank WB-200,
38 kg, bekommt den Standardtarif XL.
"""
from bestellservice import tariffs


def test_nl107_38_kg_ist_sperrgut():
    assert tariffs.tariff_for(38.0).code == "PF-SPG"
