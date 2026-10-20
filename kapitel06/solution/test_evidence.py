import json
from functools import partial

import pytest

import agent_fc
import search_rg
from evidence import verify
from llm import Reply, ToolCall
from tools import ROOT


@pytest.fixture(autouse=True)
def ohne_rg(monkeypatch):
    monkeypatch.setattr(search_rg.shutil, "which",
                        lambda name: None)


def antwort(path="bestellservice/labels.py", start=45, end=50,
            quote="weight += item[\"weight_kg\"]", **extra):
    claim = {"text": "Labelgewicht", "path": path,
             "line_start": start, "line_end": end,
             "quote": quote}
    return json.dumps({"claims": [claim], **extra})


def test_gueltiger_beleg_passiert():
    assert verify(antwort(), ROOT) == []
    assert verify("```json\n" + antwort() + "\n```", ROOT) == []


def test_falsche_zeile_und_erfundenes_zitat():
    assert "Zitat steht nicht" in verify(
        antwort(start=95, end=100), ROOT)[0]
    assert "Zitat steht nicht" in verify(
        antwort(quote="weight * quantity"), ROOT)[0]
    assert "gibt es" in verify(antwort(end=999), ROOT)[0]


def test_veraltete_readme_angabe():
    fehler = verify(antwort(path="bestellservice/porto.py"),
                    ROOT)
    assert fehler == [
        "Claim 1: bestellservice/porto.py gibt es nicht"]


def test_nicht_gefunden_ist_belegt():
    ok = json.dumps({"not_found": ["storn", "cancel"]})
    assert verify(ok, ROOT) == []
    falsch = json.dumps({"not_found": ["order_weight"]})
    assert "es gibt Treffer" in verify(falsch, ROOT)[0]


def test_ohne_beleg_und_kein_json():
    assert "ohne Beleg" in verify('{"claims": []}', ROOT)[0]
    assert "Kein gültiges" in verify("Im Modul labels.",
                                     ROOT)[0]


def test_agent_bekommt_einwand_zurueck(monkeypatch, tmp_path):
    monkeypatch.setattr(agent_fc, "TRACE", tmp_path / "t.jsonl")
    antworten = iter([
        Reply("", [ToolCall("c1", "search",
                            {"pattern": "def .*weight"})], {}),
        Reply(antwort(path="bestellservice/porto.py"), [], {}),
        Reply(antwort(), [], {})])
    gesehen = []

    def fake(messages, tools):
        gesehen.append(list(messages))
        return next(antworten)
    monkeypatch.setattr(agent_fc, "ask_model_tools", fake)
    out = agent_fc.run("Wo?", check=partial(verify, root=ROOT))
    assert out == antwort()
    assert gesehen[2][-1]["content"].startswith(
        "Antwort abgelehnt:\nClaim 1: bestellservice/porto.py")


def test_dateiverweis_ist_kein_suchbegriff():
    a = ('{"not_found": ["bestellservice/orders.py:145",'
         ' "orders.py"]}')
    fehler = verify(a, ROOT)
    assert len(fehler) == 2
    assert all("kein Suchbegriff" in f for f in fehler)
