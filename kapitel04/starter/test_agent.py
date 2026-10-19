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


def test_step_budget(monkeypatch, tmp_path):
    monkeypatch.setattr(agent, "TRACE", tmp_path / "t.jsonl")
    monkeypatch.setattr(agent, "ask_model",
                        lambda m: j("read_file", path="4711.json"))
    assert agent.run("x").startswith("ABBRUCH")


def test_pfad_ausserhalb():
    d = agent.Decision(thought="", tool="read_file",
                       args={"path": "../agent.py"})
    assert "PermissionError" in agent.execute(d)


def test_kein_json(monkeypatch, tmp_path):
    monkeypatch.setattr(agent, "TRACE", tmp_path / "t.jsonl")
    monkeypatch.setattr(agent, "ask_model", scripted(
        "Ich lese jetzt die Datei.", j("finish", answer="ok")))
    assert agent.run("x") == "ok"


def test_absolute_pfade():
    for p in ["../tools.py", "/etc/hosts", "C:/Windows/win.ini"]:
        d = agent.Decision(thought="", tool="read_file",
                           args={"path": p})
        assert "PermissionError" in agent.execute(d), p
