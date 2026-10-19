import io
import json
import urllib.error

import pytest

import llm

ANTWORT = {
    "choices": [{"message": {"content": '{"ok": true}'}}],
    "usage": {"prompt_tokens": 12, "completion_tokens": 5,
              "total_tokens": 17}}


@pytest.fixture
def leitung(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "http://test/v1")
    monkeypatch.setenv("LLM_MODEL", "testmodell")
    monkeypatch.setenv("LLM_API_KEY", "sk-geheim")
    monkeypatch.delenv("LLM_JSON_MODE", raising=False)
    monkeypatch.delenv("LLM_TEMPERATURE", raising=False)
    gesendet = []

    def fake_urlopen(req, timeout):
        gesendet.append(req)          # Anfrage festhalten
        return io.BytesIO(json.dumps(ANTWORT).encode())

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    return gesendet


def test_request_und_antwort(leitung):
    msgs = [{"role": "user", "content": "Hallo"}]
    assert llm.ask_model(msgs) == '{"ok": true}'
    req = leitung[0]
    body = json.loads(req.data)
    assert req.full_url == "http://test/v1/chat/completions"
    assert body["messages"] == msgs
    assert body["response_format"] == {"type": "json_object"}
    assert "temperature" not in body
    assert llm.LAST_USAGE["prompt_tokens"] == 12


def test_json_modus_aus_temperatur_an(leitung, monkeypatch):
    monkeypatch.setenv("LLM_JSON_MODE", "0")
    monkeypatch.setenv("LLM_TEMPERATURE", "0.7")
    llm.ask_model([{"role": "user", "content": "Hallo"}])
    body = json.loads(leitung[0].data)
    assert "response_format" not in body
    assert body["temperature"] == 0.7


def test_last_usage_in_place(leitung, monkeypatch):
    from llm import LAST_USAGE  # so importiert Kapitel 4
    llm.ask_model([{"role": "user", "content": "Hallo"}])
    assert LAST_USAGE["completion_tokens"] == 5
    # Anbieter ohne usage-Feld: alte Werte dürfen nicht bleiben
    monkeypatch.setitem(ANTWORT, "usage", None)
    llm.ask_model([{"role": "user", "content": "Hallo"}])
    assert LAST_USAGE == {}


def test_http_fehler_ohne_schluessel(leitung, monkeypatch):
    def fehler(req, timeout):
        raise urllib.error.HTTPError(
            req.full_url, 401, "Unauthorized", None,
            io.BytesIO(b'{"error": "bad key sk-geheim"}'))

    monkeypatch.setattr("urllib.request.urlopen", fehler)
    with pytest.raises(RuntimeError, match="HTTP 401") as info:
        llm.ask_model([{"role": "user", "content": "Hallo"}])
    assert "sk-geheim" not in str(info.value)
