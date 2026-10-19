"""Gibt trace.jsonl von agent_fc.py als Tabelle aus."""
import json
import sys
from pathlib import Path

pfad = sys.argv[1] if len(sys.argv) > 1 else "trace.jsonl"
text = Path(pfad).read_text(encoding="utf-8")
for line in text.splitlines():
    r = json.loads(line)
    if "abort" in r:
        print(f"{r['step']:>3}  ABBRUCH     {r['abort']}")
    elif "answer" in r:
        print(f"{r['step']:>3}  Antwort     {r['answer'][:40]}")
    else:
        args = json.dumps(r["args"], ensure_ascii=False)[:30]
        print(f"{r['step']:>3}  {r['tool']:<11} {args}")
        print(f"     -> {r['observation'][:50]!r}")
