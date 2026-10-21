import json, os, sys, time
from pathlib import Path
import agent
TASK = ("Wie hat der letzte Commit den Gesamtwert von "
        "Bestellung 4711 verändert?")
for model in sys.argv[1:]:
    os.environ["LLM_MODEL"] = model
    for i in range(3):
        tr = Path(f"traces/{model.replace(':','_')}_git_{i}.jsonl")
        tr.parent.mkdir(exist_ok=True); tr.unlink(missing_ok=True)
        agent.TRACE = tr
        t0 = time.time()
        try: ans = agent.run(TASK)
        except Exception as e: ans = f"EXC {e}"
        steps = sum(1 for _ in tr.open(encoding="utf-8")) if tr.exists() else 0
        print(json.dumps(dict(model=model, run=i, answer=ans[:120],
              steps=steps, sec=round(time.time()-t0,1)),
              ensure_ascii=False), flush=True)
