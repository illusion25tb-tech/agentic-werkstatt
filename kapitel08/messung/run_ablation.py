"""Ablation mit Ollama, llama3.2-16k, Temperatur 0,7.

Aufruf aus messung/: python run_ablation.py ohne F1,F2 3
Jede Zeile in ergebnisse.jsonl ist ein Run.
"""
import json
import os
import sys
import time
from pathlib import Path

HIER = Path(__file__).parent
SOL = HIER.parent / "solution"
sys.path.insert(0, str(SOL))
os.environ.update(LLM_BASE_URL="http://127.0.0.1:11434/v1",
                  LLM_MODEL="llama3.2-16k", LLM_TEMPERATURE="0.7")

import ablation  # noqa: E402
import llm  # noqa: E402

llm.TIMEOUT = 1800
bed, ids = sys.argv[1], sys.argv[2].split(",")
runs = int(sys.argv[3]) if len(sys.argv) > 3 else 3
alle = json.loads((SOL / "evals" / "anschlussfragen.json")
                  .read_text(encoding="utf-8"))["fragen"]
episoden = json.loads((SOL / "evals" / "episoden.json")
                      .read_text(encoding="utf-8"))
gift = json.loads((HIER / "gift.json").read_text(
    encoding="utf-8"))
episoden["gift"] = [gift]
ablation.BEDINGUNGEN = {bed: ablation.BEDINGUNGEN[bed]}


def run_one(frage, mem, name):
    t0 = time.time()
    row = ablation.run_one(frage, mem, name,
                           traces=HIER / "traces")
    row.update(sec=round(time.time() - t0),
               date=time.strftime("%Y-%m-%d"),
               model=os.environ["LLM_MODEL"])
    b, fid, i = name.split("_")
    zeile = json.dumps({"bed": b, "frage": fid, "run": int(i),
                        "memories": len(mem), **row},
                       ensure_ascii=False)
    print(zeile, flush=True)
    with (HIER / "ergebnisse.jsonl").open(
            "a", encoding="utf-8") as f:
        f.write(zeile + "\n")
    return row


fragen = [f for f in alle if f["id"] in ids]
ablation.ablate(fragen, episoden, run_one, runs)
