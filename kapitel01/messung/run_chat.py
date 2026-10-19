"""Weg 1 und 2 aus Kapitel 1: Ticket NL-101 plus Code als Chatfrage.

chat: Ticket + shipping_costs.py (was man typischerweise einfügt)
pair: Ticket + shipping_costs.py + cart.py (beide Dateien freigegeben)
Ergebnis: chat_runs.jsonl (eine Zeile pro Run).
"""
import json
import os
import re
import sys
from pathlib import Path

from llm import ask_model

CODE = Path(__file__).resolve().parents[2]
SRC = CODE / "bestellservice" / "bestellservice"
TICKET = (CODE / "issues" / "NL-101.md").read_text(encoding="utf-8")
FILES = {"chat": ["shipping_costs.py"],
         "pair": ["shipping_costs.py", "cart.py"]}
QUESTION = ("Hier ist ein Ticket und der zugehörige Code. Wo liegt die "
            "Ursache, und wie lautet die Korrektur? Antworte knapp.")


def prompt(variant: str) -> str:
    parts = [QUESTION, TICKET]
    for name in FILES[variant]:
        text = (SRC / name).read_text(encoding="utf-8")
        parts.append(f"Datei {name}:\n```python\n{text}```")
    return "\n\n".join(parts)


def classify(answer: str) -> dict:
    return {"ge": ">=" in answer,
            "decimal": "Decimal" in answer,
            "float_cause": bool(re.search(
                r"Gleitkomma|float|Rundungsfehler|49[,.]9999",
                answer, re.I))}


if __name__ == "__main__":
    os.environ.setdefault("LLM_TEMPERATURE", "0.7")
    os.environ["LLM_JSON_MODE"] = "0"
    out = Path(__file__).with_name("chat_runs.jsonl")
    models = sys.argv[1:] or ["gemma3:4b", "llama3.2:3b", "phi4-mini"]
    for model in models:
        os.environ["LLM_MODEL"] = model
        for variant in FILES:
            for run in range(1, 4):
                answer = ask_model([{"role": "user",
                                     "content": prompt(variant)}])
                rec = {"model": model, "variant": variant, "run": run,
                       **classify(answer), "answer": answer}
                with out.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                print(model, variant, run, classify(answer))
