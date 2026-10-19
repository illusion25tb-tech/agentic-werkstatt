import pytest

import agent_fc
from contracts import ToolError
from llm import Reply, ToolCall
from mcp_bridge import connect
from repo_server import mcp


def test_schema_uebersetzt_und_call_weitergeleitet():
    with connect(mcp) as bridge:
        schemas = {s["function"]["name"]: s["function"]
                   for s in bridge.schemas()}
        assert set(schemas) == {"list_files", "read_file",
                                "search"}
        params = schemas["read_file"]["parameters"]
        assert params["required"] == ["path"]
        text = bridge.call("search",
                           {"text": "def weight_class"})
        assert text == "bestellservice/tariffs.py"


def test_bridge_prueft_argumente_selbst():
    with connect(mcp) as bridge:
        for args in ({"path": 5}, {}, "kein json"):
            with pytest.raises(ToolError) as e:
                bridge.call("read_file", args)
            assert e.value.kind == "invalid_args"
        with pytest.raises(ToolError) as e:
            bridge.call("read_file", {"path": "../.env"})
        assert e.value.kind == "server"


def test_agent_kennt_nur_die_bridge(monkeypatch, tmp_path):
    monkeypatch.setattr(agent_fc, "TRACE", tmp_path / "t.jsonl")
    antworten = iter([
        Reply("", [ToolCall("c1", "search",
                            {"text": "FREE_SHIPPING"})], {}),
        Reply("shipping_costs.py", [], {})])
    gesehen = []

    def fake(messages, tools):
        gesehen.append(list(messages))
        return next(antworten)
    monkeypatch.setattr(agent_fc, "ask_model_tools", fake)
    with connect(mcp) as bridge:
        antwort = agent_fc.run("Wo?", bridge)
    assert antwort == "shipping_costs.py"
    assert "shipping_costs.py" in gesehen[1][-1]["content"]
