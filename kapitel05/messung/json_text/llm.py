"""ask_model(): Modellaufruf über eine OpenAI-kompatible API."""
import json
import os
import urllib.error
import urllib.request

LAST_USAGE: dict = {}  # Token-Angaben des letzten Aufrufs
TIMEOUT = 120  # Sekunden


def ask_model(messages: list[dict]) -> str:
    body = {"model": os.environ["LLM_MODEL"],
            "messages": messages}
    if os.environ.get("LLM_JSON_MODE", "1") != "0":
        body["response_format"] = {"type": "json_object"}
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
    return data["choices"][0]["message"]["content"]
