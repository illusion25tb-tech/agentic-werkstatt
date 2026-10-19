"""ask_model() nach dem Vertrag aus Kapitel 3, nur Standardbibliothek.

Für die Messungen in Kapitel 1 (Ollama lokal). Umgebung:
LLM_BASE_URL, LLM_MODEL, LLM_API_KEY, LLM_TEMPERATURE, LLM_JSON_MODE.
"""
import json
import os
import urllib.request

LAST_USAGE: dict = {}


def ask_model(messages: list[dict]) -> str:
    base = os.environ.get("LLM_BASE_URL", "http://127.0.0.1:11434/v1")
    body = {"model": os.environ.get("LLM_MODEL", "gemma3:4b"),
            "messages": messages}
    if "LLM_TEMPERATURE" in os.environ:
        body["temperature"] = float(os.environ["LLM_TEMPERATURE"])
    if os.environ.get("LLM_JSON_MODE", "1") == "1":
        body["response_format"] = {"type": "json_object"}
    req = urllib.request.Request(
        base.rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer "
                 + os.environ.get("LLM_API_KEY", "ollama")})
    with urllib.request.urlopen(req, timeout=600) as resp:
        data = json.load(resp)
    usage = data.get("usage") or {}
    LAST_USAGE.clear()
    LAST_USAGE.update(prompt=usage.get("prompt_tokens"),
                      completion=usage.get("completion_tokens"))
    return data["choices"][0]["message"]["content"]
