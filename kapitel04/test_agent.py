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


def test_pfad_ausserhalb(monkeypatch):
    d = agent.Decision(thought="", tool="read_file",
                       args={"path": "../agent.py"})
    assert "PermissionError" in agent.execute(d)


def test_kein_json(monkeypatch, tmp_path):
    monkeypatch.setattr(agent, "TRACE", tmp_path / "t.jsonl")
    monkeypatch.setattr(agent, "ask_model", scripted(
        "Ich lese jetzt die Datei.", j("finish", answer="ok")))
    assert agent.run("x") == "ok"


def test_repeat_abbruch(monkeypatch, tmp_path):
    import agent_hardened as ah
    monkeypatch.setattr(ah, "TRACE", tmp_path / "t.jsonl")
    calls = []
    def m(messages):
        calls.append(1)
        return j("read_file", path="4711.json")
    monkeypatch.setattr(ah, "ask_model", m)
    assert ah.run("x") == "ABBRUCH: Wiederholung ohne Fortschritt"
    assert len(calls) == 3


def test_list_files():
    from tools import list_files
    assert "bestellungen/4711.json" in list_files(".")


def test_absolute_pfade():
    for p in ["../tools.py", "/etc/hosts", "C:/Windows/win.ini"]:
        d = agent.Decision(thought="", tool="read_file",
                           args={"path": p})
        assert "PermissionError" in agent.execute(d), p


def test_repeat_nur_direkt_hintereinander(monkeypatch, tmp_path):
    import agent_hardened as ah
    monkeypatch.setattr(ah, "TRACE", tmp_path / "t.jsonl")
    calc = j("calculator")             # fehlendes Argument
    monkeypatch.setattr(ah, "ask_model", scripted(
        calc, calc, j("list_files", path="."), calc,
        j("finish", answer="ok")))
    assert ah.run("x") == "ok"


def test_fehlendes_feld_wird_benannt(monkeypatch, tmp_path):
    import agent_hardened as ah
    monkeypatch.setattr(ah, "TRACE", tmp_path / "t.jsonl")
    seen = []
    def m(messages):
        seen.append(messages[-1]["content"])
        if len(seen) == 1:
            return '{"tool": "finish", "args": {}}'
        return j("finish", answer="ok")
    monkeypatch.setattr(ah, "ask_model", m)
    assert ah.run("x") == "ok"
    assert "'thought'" in seen[1]


def test_list_files_falsches_verzeichnis():
    from tools import list_files
    import pytest
    with pytest.raises(FileNotFoundError, match="ohne"):
        list_files("workspace/")


def test_repeat_auch_bei_ungueltiger_antwort(monkeypatch, tmp_path):
    import agent_hardened as ah
    monkeypatch.setattr(ah, "TRACE", tmp_path / "t.jsonl")
    calls = []
    def m(messages):
        calls.append(1)
        return '{"tool": "finish", "args": {"answer": "x"}}'
    monkeypatch.setattr(ah, "ask_model", m)
    assert ah.run("x").startswith("ABBRUCH: Wiederholung")
    assert len(calls) == 3
