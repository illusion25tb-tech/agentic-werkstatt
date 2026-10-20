"""Kontextinventur und Compaction auf einem echten Run.

Aufruf aus messung/: python inventur.py montag [compact]
Liest traces/<tag>_requests.json (von montag_dienstag.py).
Mit "compact" läuft einmal compaction.compact mit dem echten
Zusammenfasser (llama3.2-16k, Temperatur 0,7).
"""
import json
import os
import sys
from pathlib import Path

HIER = Path(__file__).parent
sys.path.insert(0, str(HIER.parent / "solution"))
os.environ.update(LLM_BASE_URL="http://127.0.0.1:11434/v1",
                  LLM_MODEL="llama3.2-16k", LLM_TEMPERATURE="0.7")

import llm  # noqa: E402
from compaction import compact, model_summary, size  # noqa: E402
from context_builder import inventory  # noqa: E402

llm.TIMEOUT = 1800
tag = sys.argv[1]
reqs = json.loads((HIER / "traces" / f"{tag}_requests.json")
                  .read_text(encoding="utf-8"))
for i, r in enumerate(reqs, 1):
    inv = inventory(r["messages"], r["tools"])
    print(i, "geschätzt", sum(inv.values()), "gemeldet",
          r["usage"].get("prompt_tokens"), inv)
if "compact" in sys.argv:
    msgs = reqs[-1]["messages"]
    neu = compact(msgs, max_tokens=size(msgs) // 2,
                  summarize=model_summary, keep_last=2)
    print("vorher", size(msgs), "Nachrichten", len(msgs))
    print("nachher", size(neu), "Nachrichten", len(neu),
          "Zusammenfassung:", llm.LAST_USAGE)
    for m in neu:
        if (m.get("content") or "").startswith("[Zusammen"):
            print(m["content"])
    (HIER / "traces" / f"{tag}_compact.json").write_text(
        json.dumps(neu, ensure_ascii=False, indent=0),
        encoding="utf-8")
