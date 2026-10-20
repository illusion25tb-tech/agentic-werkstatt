import json

import agent


def scripted(*antworten):
    it = iter(antworten)
    return lambda messages: next(it)


def j(tool, **args):
    d = {"thought": "-", "tool": tool, "args": args}
    return json.dumps(d)


def test_happy_path(monkeypatch, tmp_path):
    monkeypatch.setattr(agent, "TRACE", tmp_path / "t.jsonl")
    monkeypatch.setattr(agent, "ask_model", scripted(
        j("read_file", path="bestellungen/4711.json"),
        j("calculator", expression="2*89.90 + 3*12.50"),
        j("finish", answer="217.3")))
    assert agent.run("Gesamtwert 4711?") == "217.3"
