"""Zwei echte Runs ohne Memory: Montag A1, Dienstag F1.

Aufruf aus messung/: python montag_dienstag.py
Speichert Traces und die Nachrichten jedes Requests, damit
Kontextinventur und Compaction auf echten Daten laufen.
"""
import json
import os
import sys
import time
from functools import partial
from pathlib import Path

HIER = Path(__file__).parent
sys.path.insert(0, str(HIER.parent / "solution"))
os.environ.update(LLM_BASE_URL="http://127.0.0.1:11434/v1",
                  LLM_MODEL="llama3.2-16k", LLM_TEMPERATURE="0.7")

import agent_fc  # noqa: E402
import llm  # noqa: E402
from ask_repo import AUFTRAG  # noqa: E402
from evidence import verify  # noqa: E402
from repo_map import repo_map  # noqa: E402
from tools import ROOT  # noqa: E402

llm.TIMEOUT = 1800
FRAGEN = json.loads((HIER.parent / "solution" / "evals" /
                     "anschlussfragen.json").read_text(
                         encoding="utf-8"))
TAGE = {"montag": FRAGEN["montag"],
        "dienstag": FRAGEN["fragen"][0]["frage"]}
echt = agent_fc.ask_model_tools
for tag, frage in TAGE.items():
    requests = []

    def mitschnitt(messages, tools):
        reply = echt(messages, tools)
        requests.append({"messages": [dict(m) for m in messages],
                         "tools": tools,
                         "usage": dict(llm.LAST_USAGE)})
        return reply
    agent_fc.ask_model_tools = mitschnitt
    agent_fc.TRACE = HIER / "traces" / f"{tag}.jsonl"
    agent_fc.TRACE.unlink(missing_ok=True)
    t0 = time.time()
    task = AUFTRAG.format(frage=frage, karte=repo_map(ROOT))
    ans = agent_fc.run(task, check=partial(verify, root=ROOT))
    print(tag, round(time.time() - t0), "s:", ans[:300])
    (HIER / "traces" / f"{tag}_requests.json").write_text(
        json.dumps(requests, ensure_ascii=False, indent=0),
        encoding="utf-8")
