"""Messung Einstieg: NL-104 fünfmal je Modell (echte Runs, Ollama)."""
import json, os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "solution"))
import llm
llm.TIMEOUT = 900
from streuung import FRAGE

ticket = (Path(__file__).parents[2] / "issues/NL-104.md").read_text(encoding="utf-8")
out = Path(__file__).parent / sys.argv[1]
os.environ.update(LLM_BASE_URL="http://127.0.0.1:11434/v1", LLM_JSON_MODE="0")
with out.open("w", encoding="utf-8") as f:
    for model in ["gemma3:4b", "llama3.2:3b", "phi4-mini"]:
        os.environ["LLM_MODEL"] = model
        for run in range(1, 6):
            a = llm.ask_model([{"role": "user", "content": FRAGE + ticket}])
            rec = {"model": model, "run": run, "temperature": os.environ.get("LLM_TEMPERATURE"),
                   "answer": a, "usage": dict(llm.LAST_USAGE), "ts": time.strftime("%Y-%m-%d %H:%M")}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
            print(model, run, " ".join(a.split())[:150])
