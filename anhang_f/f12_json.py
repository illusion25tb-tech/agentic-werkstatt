"""JSON schreiben und lesen."""

import json

rec = {"tool": "read_file", "args": {"path": "cart.py"},
       "ok": True}
line = json.dumps(rec)
print(line)
back = json.loads(line)
print(back["args"]["path"], back["ok"])
print(json.loads('{"note": null, "ok": false}'))

print(json.dumps({"größe": "XL"}))
print(json.dumps({"größe": "XL"}, ensure_ascii=False))

try:
    json.loads("{tool: read_file}")
except json.JSONDecodeError as e:
    print("FEHLER:", e.msg)
