import json

import agent
from tools_guard import LEER, guard


def scripted(*antworten):
    it = iter(antworten)

    def ask(messages):
        agent.LAST_USAGE.clear()
        agent.LAST_USAGE.update(prompt_tokens=100,
                                completion_tokens=20)
        return next(it)
    return ask


def j(tool, **args):
    return json.dumps({"thought": "-", "tool": tool,
                       "args": args})


def by_name(spans):
    return {s.name: s for s in spans()}


def test_hierarchie_und_token(monkeypatch, tmp_path, spans):
    monkeypatch.setattr(agent, "TRACE", tmp_path / "t.jsonl")
    monkeypatch.setattr(agent, "MODEL", "m")
    monkeypatch.setattr(agent, "ask_model", scripted(
        j("read_file", path="bestellungen/4711.json"),
        j("finish", answer="217.3")))
    assert agent.run("Gesamtwert 4711?") == "217.3"
    s = by_name(spans)
    root = s["invoke_agent agent"]
    tool = s["execute_tool read_file"]
    chats = [x for x in spans() if x.name == "chat m"]
    assert len(chats) == 2
    assert tool.parent.span_id == root.context.span_id
    tin = chats[0].attributes["gen_ai.usage.input_tokens"]
    assert tin == 100
    assert tool.attributes["gen_ai.tool.name"] == "read_file"
    assert tool.status.is_ok


def test_leerer_string_wird_fehler(monkeypatch, tmp_path,
                                   spans):
    monkeypatch.setattr(agent, "TRACE", tmp_path / "t.jsonl")
    monkeypatch.setitem(agent.TOOLS, "read_file",
                        lambda path: "")
    monkeypatch.setattr(agent, "ask_model", scripted(
        j("read_file", path="bestellungen/4711.json"),
        j("finish", answer="?")))
    agent.run("Gesamtwert 4711?")
    tool = by_name(spans)["execute_tool read_file"]
    assert not tool.status.is_ok
    assert tool.attributes["error.type"] == "empty"
    zeile = (tmp_path / "t.jsonl").read_text(encoding="utf-8")
    assert "FEHLER [leer]" in zeile


def test_guard():
    assert guard("") == LEER and guard("  \n") == LEER
    assert guard(None) == LEER
    assert guard("0 Treffer in 12 Dateien") != LEER


def test_kein_inhalt_im_span(monkeypatch, tmp_path, spans):
    monkeypatch.setattr(agent, "TRACE", tmp_path / "t.jsonl")
    monkeypatch.setattr(agent, "ask_model", scripted(
        j("finish", answer="geheim")))
    agent.run("Auftrag mit Kundendaten")
    for s in spans():
        text = json.dumps(dict(s.attributes))
        assert "Kundendaten" not in text
        assert "geheim" not in text


def luegt(fn):
    calls = {"n": 0}

    def wrapper(**kw):
        calls["n"] += 1
        return "" if calls["n"] % 3 == 0 else fn(**kw)
    return wrapper


def test_jeder_dritte_aufruf_leer(monkeypatch, tmp_path, spans):
    monkeypatch.setattr(agent, "TRACE", tmp_path / "t.jsonl")
    monkeypatch.setitem(agent.TOOLS, "read_file",
                        luegt(lambda path: "Inhalt"))
    lies = j("read_file", path="bestellungen/4711.json")
    monkeypatch.setattr(agent, "ask_model", scripted(
        lies, j("calculator", expression="1"), lies, lies,
        j("finish", answer="ok")))
    agent.run("x")
    tools = [x for x in spans() if x.name.startswith("execute")]
    status = [x.status.is_ok for x in tools]
    assert status == [True, True, True, False]
