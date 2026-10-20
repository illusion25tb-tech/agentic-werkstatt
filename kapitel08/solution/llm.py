"""ask_model() aus Kapitel 3, dazu natives Function Calling."""
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field

LAST_USAGE: dict = {}  # Token-Angaben des letzten Aufrufs
TIMEOUT = 120  # Sekunden


def _post(body: dict) -> dict:
    """Wie ask_model() in Kapitel 3, nur ohne Auswertung."""
    body["model"] = os.environ["LLM_MODEL"]
    temp = os.environ.get("LLM_TEMPERATURE")
    if temp:                      # nur senden, wenn gesetzt
        body["temperature"] = float(temp)
    key = os.environ.get("LLM_API_KEY", "")
    url = os.environ["LLM_BASE_URL"].rstrip("/")
    req = urllib.request.Request(
        url + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8", "replace")[:300]
        if key:
            text = text.replace(key, "***")
        raise RuntimeError(f"HTTP {e.code}: {text}") from None
    LAST_USAGE.clear()
    LAST_USAGE.update(data.get("usage") or {})
    return data


def ask_model(messages: list[dict]) -> str:
    body = {"messages": messages}
    if os.environ.get("LLM_JSON_MODE", "1") != "0":
        body["response_format"] = {"type": "json_object"}
    data = _post(body)
    return data["choices"][0]["message"]["content"]


@dataclass
class ToolCall:
    id: str
    name: str
    args: dict | str    # str: kein gültiges JSON vom Modell


@dataclass
class Reply:
    text: str
    calls: list[ToolCall] = field(default_factory=list)
    message: dict = field(default_factory=dict)  # Verlauf


def ask_model_tools(messages: list[dict],
                    tools: list[dict]) -> Reply:
    data = _post({"messages": messages, "tools": tools})
    msg = data["choices"][0]["message"]
    calls = []
    for c in msg.get("tool_calls") or []:
        raw = c["function"].get("arguments") or "{}"
        try:
            args = json.loads(raw)
        except json.JSONDecodeError:
            args = raw
        calls.append(ToolCall(c["id"], c["function"]["name"],
                              args))
    keep = {k: msg[k] for k in ("role", "content", "tool_calls")
            if msg.get(k) is not None}
    return Reply(msg.get("content") or "", calls, keep)
