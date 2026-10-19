"""Messung Praxis-Box: Break- gegen Harden-Fassung, 20 Issues x 2 Runs.

Echte Runs gegen Ollama. Ergebnis als JSON Lines in messung/.
Aufruf: python messung/klassifizierer.py break|harden
"""
import json, os, sys, time
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "solution"))
import llm
llm.TIMEOUT = 900
import classify
from schema import IssueKlasse
from pydantic import ValidationError

BREAK_SYSTEM = ("Ordne das Ticket eines Online-Shops ein. Antworte als JSON "
                "mit den Feldern kategorie, prioritaet und begruendung.")
varianten = sys.argv[1].split(",")
modelle = sys.argv[2].split(",") if len(sys.argv) > 2 else ["gemma3:4b", "llama3.2:3b", "phi4-mini"]
issues = sorted((HERE.parents[1] / "issues").glob("NL-1[0-1][0-9].md"))[:5]  # GPU geteilt: nur NL-101 bis NL-105
os.environ.update(LLM_BASE_URL="http://127.0.0.1:11434/v1", LLM_TEMPERATURE="1.5")
out = HERE / "klassifizierer.jsonl"
fertig = {(r["variante"], r["model"], r["run"], r["issue"]) for r in map(json.loads, out.open(encoding="utf-8"))} if out.exists() else set()
with out.open("a", encoding="utf-8") as f:
    for model in modelle:
        os.environ["LLM_MODEL"] = model
        for run in (1, 2):
            for p in issues:
              for variante in varianten:
                if (variante, model, run, p.stem) in fertig:
                    continue
                os.environ["LLM_JSON_MODE"] = "0" if variante == "break" else "1"
                text = p.read_text(encoding="utf-8")
                rec = {"variante": variante, "model": model, "run": run, "issue": p.stem,
                       "temperature": 1.5, "json_mode": os.environ["LLM_JSON_MODE"],
                       "ts": time.strftime("%Y-%m-%d %H:%M")}
                if variante == "break":
                    try:
                        raw = llm.ask_model([{"role": "system", "content": BREAK_SYSTEM},
                                             {"role": "user", "content": text}])
                    except TimeoutError:
                        raw = "TIMEOUT nach 900 s"
                        llm.LAST_USAGE.clear()
                    rec["calls"] = 1
                    rec["tokens_in"] = llm.LAST_USAGE.get("prompt_tokens", 0)
                    rec["tokens_out"] = llm.LAST_USAGE.get("completion_tokens", 0)
                    try:
                        k = IssueKlasse.model_validate_json(raw)
                        rec.update(valid=True, kategorie=k.kategorie, prioritaet=k.prioritaet)
                    except ValidationError as e:
                        rec.update(valid=False, fehler=e.errors()[0]["type"])
                    rec["raw"] = raw[:400]
                else:
                    before = dict(classify.TOKENS)
                    calls = []
                    orig = classify.ask_model
                    def wrapped(m, _o=orig):
                        r = _o(m); calls.append(r[:400]); return r
                    classify.ask_model = wrapped
                    try:
                        k = classify.classify(text)
                        rec.update(valid=True, kategorie=k.kategorie, prioritaet=k.prioritaet)
                    except (ValueError, TimeoutError) as e:
                        rec.update(valid=False, fehler=(str(e) or type(e).__name__)[:120])
                    finally:
                        classify.ask_model = orig
                    rec["calls"] = len(calls)
                    rec["tokens_in"] = classify.TOKENS["prompt_tokens"] - before.get("prompt_tokens", 0)
                    rec["tokens_out"] = classify.TOKENS["completion_tokens"] - before.get("completion_tokens", 0)
                    rec["raw"] = calls
                f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
                print(model, run, p.stem, rec["valid"], rec.get("kategorie"), rec["calls"], flush=True)
