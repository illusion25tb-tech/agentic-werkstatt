"""Gibt trace.jsonl als lesbare Tabelle aus."""
import json
import sys

pfad = sys.argv[1] if len(sys.argv) > 1 else "trace.jsonl"
for line in open(pfad, encoding="utf-8"):
    r = json.loads(line)
    if "abort" in r:
        print(f"{r['step']:>3}  ABBRUCH    {r['abort']}")
        continue
    if r.get("tool") == "finish":
        print(f"{r['step']:>3}  finish     {r['answer'][:40]}")
        continue
    d = json.loads(r["raw"]) if r["raw"].startswith("{") else {}
    tool = d.get("tool", "?")
    obs = r["observation"][:40]
    print(f"{r['step']:>3}  {tool:<10} {obs!r}")
