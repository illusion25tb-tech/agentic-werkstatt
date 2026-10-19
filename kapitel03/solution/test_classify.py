import json

import pytest
from pydantic import ValidationError

import classify
from schema import IssueKlasse

GUT = json.dumps({"kategorie": "bug", "prioritaet": "hoch",
                  "begruendung": "Betrag falsch bei Firmen."})
FALSCH = json.dumps({"kategorie": "fehler",   # nicht im Enum
                     "prioritaet": "hoch",
                     "begruendung": "Kategorie unbekannt."})


def scripted(*antworten):
    it = iter(antworten)
    return lambda messages: next(it)


@pytest.fixture
def ticket(tmp_path):
    pfad = tmp_path / "NL-104.md"
    pfad.write_text("Betrag stimmt nicht", encoding="utf-8")
    return str(pfad)


def test_gueltig_beim_ersten_mal(monkeypatch, ticket, capsys):
    monkeypatch.setattr(classify, "ask_model", scripted(GUT))
    assert classify.main([ticket]) == 0
    zeile = json.loads(capsys.readouterr().out)
    assert zeile["issue"] == "NL-104"
    assert zeile["kategorie"] == "bug"


def test_ungueltig_dann_gueltig(monkeypatch, ticket):
    gesehen = []

    def modell(messages):
        gesehen.append(list(messages))
        return [FALSCH, GUT][len(gesehen) - 1]

    monkeypatch.setattr(classify, "ask_model", modell)
    assert classify.main([ticket]) == 0
    rueckmeldung = gesehen[1][-1]["content"]   # zweiter Aufruf
    assert "kategorie" in rueckmeldung


def test_zweimal_ungueltig_exit_1(monkeypatch, ticket, capsys):
    monkeypatch.setattr(classify, "ask_model",
                        scripted("Das hängt davon ab.", FALSCH))
    assert classify.main([ticket]) == 1
    assert "fehler" in json.loads(capsys.readouterr().out)


@pytest.mark.parametrize("feld, wert", [
    ("prioritaet", "dringend"), ("begruendung", "kurz"),
    ("kategorie", "Bug")])
def test_schema_lehnt_ab(feld, wert):
    daten = json.loads(GUT) | {feld: wert}
    with pytest.raises(ValidationError):
        IssueKlasse.model_validate(daten)
