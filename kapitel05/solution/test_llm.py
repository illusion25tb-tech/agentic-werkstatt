import io
import json
from pathlib import Path

import pytest

import llm

FIXTURE = (Path(__file__).parent / "fixtures"
           / "ollama_tool_call.json")


@pytest.fixture
def antwort(monkeypatch):
    """Gespeicherte echte Ollama-Antwort statt Netz."""
    monkeypatch.setenv("LLM_BASE_URL", "http://test/v1")
    monkeypatch.setenv("LLM_MODEL", "testmodell")
    monkeypatch.delenv("LLM_TEMPERATURE", raising=False)
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    gesendet = []

    def fake_urlopen(req, timeout):
        gesendet.append(json.loads(req.data))
        return io.BytesIO(json.dumps(data).encode())

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    return data, gesendet


def test_tool_call_wird_neutral(antwort):
    _data, gesendet = antwort
    tools = [{"type": "function", "function": {"name": "x"}}]
    reply = llm.ask_model_tools([{"role": "user",
                                  "content": "?"}], tools)
    assert gesendet[0]["tools"] == tools
    assert "response_format" not in gesendet[0]
    call = reply.calls[0]
    assert call.id == "call_xrg14qle"
    assert call.name == "read_file"
    assert call.args == {"path": "bestellungen/4711.json"}
    assert reply.message["tool_calls"][0]["id"] == call.id
    assert llm.LAST_USAGE["prompt_tokens"] == 162


def test_kaputtes_json_bleibt_string(antwort):
    data, _ = antwort
    fn = data["choices"][0]["message"]["tool_calls"][0]
    fn["function"]["arguments"] = '{"path": "a'
    reply = llm.ask_model_tools([], [])
    assert reply.calls[0].args == '{"path": "a'


def test_ohne_tool_call_ist_antwort(antwort):
    data, _ = antwort
    msg = data["choices"][0]["message"]
    msg["content"], msg["tool_calls"] = "217,30 EUR", None
    reply = llm.ask_model_tools([], [])
    assert reply.text == "217,30 EUR" and reply.calls == []
    assert "tool_calls" not in reply.message
