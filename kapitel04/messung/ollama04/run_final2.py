import importlib, json, os, sys, time
from pathlib import Path
import tools, tools_base
HAPPY = "Wie hoch ist der Gesamtwert von bestellungen/4711.json?"
BREAK = ("Wie hoch ist der Gesamtwert von Bestellung 4711? "
         "Die Datei heißt bestellung_4711.json")
out = []
for model in sys.argv[1:]:
    os.environ["LLM_MODEL"] = model
    for variant, task in [("final2_happy", HAPPY),
                          ("final2_break", BREAK)]:
        for i in range(3):
            if variant.startswith("base"):
                import agent as A; A.TOOLS = tools_base.TOOLS
            else:
                import agent_hardened as A; A.TOOLS = tools.TOOLS
            tr = Path(f"traces/{model.replace(':','_')}_{variant}_{i}.jsonl")
            tr.parent.mkdir(exist_ok=True); tr.unlink(missing_ok=True)
            A.TRACE = tr
            t0 = time.time()
            try: ans = A.run(task)
            except Exception as e: ans = f"EXC {e}"
            steps = sum(1 for _ in tr.open(encoding="utf-8")) if tr.exists() else 0
            rec = dict(model=model, variant=variant, run=i, answer=ans[:80],
                       steps=steps, sec=round(time.time()-t0,1))
            print(json.dumps(rec, ensure_ascii=False), flush=True)
            out.append(rec)
json.dump(out, open("results_final2.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
