import json
from pathlib import Path

from paketfix.retrieve import check_quote, chunks, retrieve
from tools import ROOT

KORPUS = ROOT / "docs" / "paketfix"
MANIFEST = Path(__file__).parent / "paketfix" / "manifest.json"


def test_sendungsnummer_aus_der_api_beschreibung():
    treffer = retrieve("Sendungsnummer", chunks(KORPUS))
    assert treffer[0]["doc"] == "paketfix_api_v2.md"
    assert "6. Sendungsnummer" in [t["section"]
                                   for t in treffer]


def test_jedes_dokument_im_manifest():
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    im_manifest = {d["datei"] for d in m["dokumente"]}
    assert im_manifest == {f.name for f in KORPUS.glob("*.md")}
    for d in m["dokumente"]:
        assert d["personenbezug"] in ("nein", "synthetisch")


def test_belegpflicht_fuer_dokumente():
    cs = chunks(KORPUS)
    doc, sec = "aenderungsprotokoll.md", (
        "Version 2.3 (gültig ab 01.09.2026)")
    assert check_quote(doc, sec, "dürfen jetzt 35 statt 30",
                       cs) is None
    assert "steht nicht" in check_quote(doc, sec, "40 Zeichen",
                                        cs)
    assert "gibt es" in check_quote(doc, "Version 9", "x", cs)
