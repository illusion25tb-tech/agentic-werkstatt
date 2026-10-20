from pathlib import Path

import pytest

from memory import open_db
from paketfix.retrieve import chunks
from redact import redact
from semantic import learn, load_versions, stale
from tools import ROOT

CS = chunks(ROOT / "docs" / "paketfix")
V = load_versions(Path(__file__).parent / "paketfix" /
                  "manifest.json")
DS = "datenschutz_paketfix.md"


def abschnitt(doc: str, titel: str) -> str:
    return next(c["text"] for c in CS
                if (c["doc"], c["section"]) == (doc, titel))


def test_beispiel_aus_der_api_doku():
    roh = abschnitt("paketfix_api_v2.md", "7. Beispiel")
    assert "Erika Musterfrau" in roh
    sauber = redact(roh)
    assert "Erika Musterfrau" not in sauber
    assert "Musterstraße 1" not in sauber
    assert '"plz": "01067"' in sauber   # keine Person
    assert "PF-STD-S" in sauber


def test_kontakt_aus_der_datenschutzrichtlinie():
    sauber = redact(abschnitt(DS, "1. Verantwortliche Stelle"))
    assert "Max Mustermann" not in sauber
    assert "@paketfix.example" not in sauber
    assert "[NAME]" in sauber and "[E-MAIL]" in sauber


def test_telefonnummer_aber_keine_postleitzahl():
    assert redact("Tel. 0521 123456-7, PLZ 01067") == (
        "Tel. [TELEFON], PLZ 01067")


def test_fakt_nur_mit_beleg_und_geschwaerzt():
    conn = open_db()
    learn(conn, "Telefonnummern nimmt die API nicht an.", DS,
          "3. Welche Daten verarbeitet werden",
          "Telefonnummern werden über die API nicht "
          "angenommen.",
          CS, V)
    learn(conn, "Datenschutzbeauftragter laut Richtlinie", DS,
          "1. Verantwortliche Stelle",
          "Max Mustermann, erreichbar unter", CS, V)
    zitate = [r["quote"] for r in conn.execute(
        "SELECT quote FROM facts")]
    assert zitate[1] == "[NAME], erreichbar unter"
    with pytest.raises(ValueError, match="steht nicht"):
        learn(conn, "Telefon ist Pflicht", DS,
              "3. Welche Daten verarbeitet werden",
              "Telefon ist Pflicht", CS, V)


def test_neue_dokumentversion_macht_fakten_alt():
    conn = open_db()
    learn(conn, "Avis nur mit Einwilligung", DS,
          "3. Welche Daten verarbeitet werden",
          "Die Avis-E-Mail ist freiwillig.", CS, V)
    assert stale(conn, V) == []
    assert len(stale(conn, V | {DS: "1.5"})) == 1
