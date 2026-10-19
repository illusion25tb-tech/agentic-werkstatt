import json
from itertools import count

import pytest

import agent_fc
from contracts import Registry
from llm import Reply, ToolCall
from tools import ALL

ids = count(1)


def call(name, **args):
    """Antwort mit genau einem Tool Call."""
    c = ToolCall(f"call_{next(ids)}", name, args)
    return Reply("", [c], {"role": "assistant"})


def done(text):
    return Reply(text, [], {"role": "assistant",
                            "content": text})


@pytest.fixture
def modell(monkeypatch, tmp_path):
    """Skript statt Modell; merkt sich jede Anfrage."""
    trace = tmp_path / "t.jsonl"
    monkeypatch.setattr(agent_fc, "TRACE", trace)
    gesehen = []

    def setze(*antworten):
        it = iter(antworten)

        def fake(messages, tools):
            gesehen.append((list(messages), tools))
            return next(it)
        monkeypatch.setattr(agent_fc, "ask_model_tools", fake)
    return setze, gesehen, trace


def test_happy_path(modell):
    setze, gesehen, trace = modell
    rechnen = call("calculator", expression="2*89.90 + 3*12.50")
    setze(call("read_file", path="bestellungen/4711.json"),
          rechnen, done("217,30 EUR"))
    assert agent_fc.run("Gesamtwert 4711?") == "217,30 EUR"
    messages, tools = gesehen[-1]
    assert messages[-1] == {"role": "tool", "content": "217.3",
                            "tool_call_id": rechnen.calls[0].id}
    assert {t["function"]["name"] for t in tools} >= {
        "read_file", "calculator"}
    zeilen = trace.read_text(encoding="utf-8").splitlines()
    assert json.loads(zeilen[0])["tool_call_id"].startswith(
        "call_")


def test_unbekanntes_tool_wird_observation(modell):
    setze, gesehen, _trace = modell
    setze(call("write_file", path="x"), done("ok"))
    assert agent_fc.run("x") == "ok"
    obs = gesehen[1][0][-1]
    assert obs["role"] == "tool"
    assert obs["content"].startswith("FEHLER [unknown_tool]")


def test_ungueltige_argumente_werden_observation(modell):
    setze, gesehen, trace = modell
    setze(call("read_file", pfad="4711.json"), done("ok"))
    assert agent_fc.run("x") == "ok"
    assert "invalid_args" in gesehen[1][0][-1]["content"]
    rec = json.loads(trace.read_text(
        encoding="utf-8").splitlines()[0])
    assert rec["error"] == "invalid_args"


def test_step_budget(modell):
    setze, _, _ = modell
    setze(*[call("calculator", expression=str(i))
            for i in range(20)])
    assert agent_fc.run("x") == "ABBRUCH: Step-Budget erschöpft"


def test_wiederholung(modell):
    setze, gesehen, _ = modell
    setze(*[call("read_file", path="4711.json")
            for _ in range(20)])
    assert agent_fc.run("x").startswith("ABBRUCH: Wiederholung")
    assert len(gesehen) == 3


nur_lesen = Registry([s for s in ALL
                      if s.name in {"read_file", "list_files"}])


def test_kleinere_registry_fuer_kleine_aufgabe(modell):
    setze, gesehen, _ = modell
    setze(done("ok"))
    agent_fc.run("Was steht in bestellungen/4711.json?",
                 nur_lesen)
    namen = {t["function"]["name"] for t in gesehen[0][1]}
    assert namen == {"read_file", "list_files"}
