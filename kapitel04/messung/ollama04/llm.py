import json, os, urllib.request
LAST_USAGE: dict = {}
def ask_model(messages):
    body = {"model": os.environ["LLM_MODEL"], "messages": messages,
            "response_format": {"type": "json_object"}, "temperature": 0.7}
    req = urllib.request.Request(
        "http://127.0.0.1:11434/v1/chat/completions",
        data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.load(r)
    LAST_USAGE.clear(); LAST_USAGE.update(d.get("usage", {}))
    return d["choices"][0]["message"]["content"]
