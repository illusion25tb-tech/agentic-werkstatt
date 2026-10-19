"""Echter Request/Response gegen Ollama für den Abschnitt 'Ein Modellaufruf ist ein HTTP-Request'."""
import json, urllib.request
body = {"model": "gemma3:4b",
        "messages": [{"role": "system", "content": "Antworte nur mit JSON."},
                     {"role": "user", "content": "Ticket: PLZ 01067 steht auf dem Label als 1067. Feld kategorie: bug oder feature?"}],
        "response_format": {"type": "json_object"}}
req = urllib.request.Request("http://127.0.0.1:11434/v1/chat/completions",
                             data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
resp = json.loads(urllib.request.urlopen(req, timeout=900).read())
out = {"request": body, "response": resp}
open("messung/request_beispiel_roh.json", "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
print(json.dumps(out, ensure_ascii=False))
