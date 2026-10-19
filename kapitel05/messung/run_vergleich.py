"""Vergleich JSON-Text (Kapitel 4) gegen natives Function Calling.

Vorher in messung/: python ../solution/setup_workspace.py
Aufruf aus messung/:  python run_vergleich.py json_text llama3.2:3b
                      python run_vergleich.py fc qwen3:4b
Ollama lokal, LLM_TEMPERATURE=0.7, je 3 Runs.
"""
import json
import os
import sys
import time
from pathlib import Path

HIER = Path(__file__).parent
variant, model = sys.argv[1], sys.argv[2]
task_name = sys.argv[3] if len(sys.argv) > 3 else "git"
TASKS = {
    "git": ("Wie hat der letzte Commit den Gesamtwert von "
            "Bestellung 4711 verändert?"),
    "summe": "Wie hoch ist der Gesamtwert von bestellungen/4711.json?",
}
os.environ.update(LLM_BASE_URL="http://127.0.0.1:11434/v1",
                  LLM_MODEL=model, LLM_TEMPERATURE="0.7")
src = HIER / "json_text" if variant == "json_text" else (
    HIER.parent / "solution")
sys.path.insert(0, str(src))
import llm  # noqa: E402
llm.TIMEOUT = 900
if variant == "json_text":
    import agent as A  # noqa: E402
else:
    import agent_fc as A  # noqa: E402
if model.startswith("qwen3"):
    A.SYSTEM += "\n/no_think"

out = HIER / "traces"
out.mkdir(exist_ok=True)
for i in range(3):
    tr = out / f"{variant}_{task_name}_{model.replace(':', '_')}_{i}.jsonl"
    tr.unlink(missing_ok=True)
    A.TRACE = tr
    t0 = time.time()
    try:
        ans = A.run(TASKS[task_name])
    except Exception as e:
        ans = f"EXC {type(e).__name__}: {e}"
    rec = dict(variant=variant, task=task_name, model=model, run=i,
               answer=ans[:300], sec=round(time.time() - t0, 1),
               date=time.strftime("%Y-%m-%d"))
    print(json.dumps(rec, ensure_ascii=False), flush=True)
    with (HIER / "ergebnisse.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
