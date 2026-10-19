"""Messung Sampling: NL-104, Antwort auf ein Wort beschränkt, T=0 und T=1, 5 Runs je Modell."""
import json, os, sys, time
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "solution"))
import llm
llm.TIMEOUT = 900
import streuung
ticket = (HERE.parents[1] / "issues/NL-104.md").read_text(encoding="utf-8")
streuung.FRAGE = ("Welche Priorität hat dieses Ticket? Antworte nur mit "
                  "einem Wort: niedrig, mittel oder hoch.\n\n")
os.environ.update(LLM_BASE_URL="http://127.0.0.1:11434/v1", LLM_JSON_MODE="0")
with (HERE / "streuung_temp.jsonl").open("w", encoding="utf-8") as f:
    for temp in ("0", "1.0"):
        os.environ["LLM_TEMPERATURE"] = temp
        for model in ["gemma3:4b", "llama3.2:3b", "phi4-mini"]:
            os.environ["LLM_MODEL"] = model
            c = streuung.streuung(ticket, 5)
            rec = {"model": model, "temperature": temp, "runs": 5, "counts": dict(c),
                   "frage": streuung.FRAGE.strip(), "ts": time.strftime("%Y-%m-%d %H:%M")}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
            print(rec, flush=True)
