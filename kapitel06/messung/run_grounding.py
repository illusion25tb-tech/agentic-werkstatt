"""Architekturfragen an den bestellservice, mit/ohne Grounding.

Aufruf aus messung/:
  python run_grounding.py mit llama3.2-16k A1 3
  python run_grounding.py ohne qwen3-16k A1 3
Ollama lokal, LLM_TEMPERATURE=0.7. Modelle mit num_ctx 16384
(Modelfile.*). Jede Zeile in ergebnisse.jsonl ist ein Run.
"""
import json
import os
import sys
import time
from functools import partial
from pathlib import Path

from pydantic import Field

HIER = Path(__file__).parent
SOL = HIER.parent / "solution"
sys.path.insert(0, str(SOL))
cond, model, qid = sys.argv[1], sys.argv[2], sys.argv[3]
runs = int(sys.argv[4]) if len(sys.argv) > 4 else 1
os.environ.update(LLM_BASE_URL="http://127.0.0.1:11434/v1",
                  LLM_MODEL=model, LLM_TEMPERATURE="0.7")

import agent_fc
import llm
from ask_repo import AUFTRAG
from contracts import Registry, ToolSpec
from evidence import Answer, check_claim, verify
from explore_metrics import metrics
from read_lines import im_repo
from repo_map import repo_map
from tools import GROUNDING, ROOT, Args

llm.TIMEOUT = 1800
if model.startswith("qwen3"):
    agent_fc.SYSTEM += "\n/no_think"


# --- Werkzeuge wie in Kapitel 5 (ohne Grounding) ---
class P(Args):
    path: str = Field(".", description="relativ zum Repo")


class S(Args):
    text: str
    path: str = "."


def k5_list(path="."):
    base = im_repo(path, ROOT)
    fs = [f.relative_to(ROOT).as_posix() for f in sorted(
        base.rglob("*")) if f.is_file() and not any(
        p.startswith(".") or p == "__pycache__"
        for p in f.relative_to(ROOT).parts)]
    return "\n".join(fs[:200])


def k5_read(path):
    t = im_repo(path, ROOT)
    if not t.is_file():
        raise FileNotFoundError(f"{path} gibt es nicht.")
    return t.read_text(encoding="utf-8")[:4000]


def k5_search(text, path="."):
    hits = [f for f in k5_list(path).splitlines()
            if text.lower() in (ROOT / f).read_text(
                encoding="utf-8", errors="ignore").lower()]
    return "\n".join(hits[:50]) or "Keine Treffer."


KAP5 = Registry([
    ToolSpec("list_files", "Listet Dateien unter path, "
             "höchstens 200.", P, k5_list),
    ToolSpec("read_file", "Liest eine Textdatei, höchstens "
             "4.000 Zeichen.", P, k5_read),
    ToolSpec("search", "Nennt Dateien, die text enthalten, "
             "höchstens 50.", S, k5_search),
])

fragen = {f["id"]: f for f in json.loads(
    (SOL / "evals" / "architekturfragen.json").read_text(
        encoding="utf-8"))["fragen"]}
frage = fragen[qid]
karte = repo_map(ROOT) if cond == "mit" else (
    "(keine Repo Map; list_files zeigt Dateien)")
task = AUFTRAG.format(frage=frage["frage"], karte=karte)
box = GROUNDING if cond == "mit" else KAP5


def bewerten(ans: str) -> dict:
    if ans.startswith(("ABBRUCH", "EXC")):
        return {"angenommen": False}
    a = Answer.model_validate_json(
        ans[ans.find("{"):ans.rfind("}") + 1])
    ok = [c for c in a.claims if check_claim(c, ROOT) is None]
    treffer = any(c.path == p and c.line_start <= e
                  and s <= c.line_end
                  for c in ok for p, s, e in frage["belege"])
    if frage.get("erwartet") == "not_found":
        treffer = bool(a.not_found)
    return {"angenommen": True, "claims": len(a.claims),
            "not_found": a.not_found, "trifft_beleg": treffer}


out = HIER / "traces"
out.mkdir(exist_ok=True)
for i in range(runs):
    name = f"{cond}_{qid}_{model.replace(':', '_')}_{i}.jsonl"
    tr = out / name
    tr.unlink(missing_ok=True)
    agent_fc.TRACE = tr
    t0 = time.time()
    try:
        ans = agent_fc.run(task, box,
                           check=partial(verify, root=ROOT))
    except Exception as e:  # noqa: BLE001
        ans = f"EXC {type(e).__name__}: {e}"
    recs = [json.loads(z) for z in tr.read_text(
        encoding="utf-8").splitlines()] if tr.exists() else []
    pt = [r["usage"].get("prompt_tokens", 0) for r in recs
          if r.get("usage")]
    rec = dict(cond=cond, model=model, frage=qid, run=i,
               answer=ans[:600], sec=round(time.time() - t0),
               date=time.strftime("%Y-%m-%d"),
               einwaende=sum(1 for r in recs if r.get("rejected")),
               max_prompt_tokens=max(pt, default=0),
               **bewerten(ans),
               **(metrics(tr, set(frage["relevant"]))
                  if tr.exists() else {}))
    print(json.dumps(rec, ensure_ascii=False), flush=True)
    with (HIER / "ergebnisse.jsonl").open(
            "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
