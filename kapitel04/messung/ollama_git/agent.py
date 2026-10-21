"""Minimaler Agent Loop: beobachten, entscheiden, handeln."""
import json
import time
from pathlib import Path

from pydantic import BaseModel, ValidationError

from llm import LAST_USAGE, ask_model  # aus Kapitel 3
from tools import TOOLS

MAX_STEPS = 12
MAX_REPEATS = 2
TRACE = Path("trace.jsonl")

SYSTEM = """Du bist ein Agent. Antworte nur mit einem JSON-Objekt:
{"thought": "...", "tool": "<name>", "args": {...}}
Verfügbare Tools:
- calculator(expression): rechnet mit + - * / ( )
- read_file(path): liest eine Datei, z. B. "bestellungen/1.json"
- list_files(path): listet Dateien, "." für alle
- git(command): liest das Repository mit status, log, show,
  diff, ls-files oder grep, z. B. "show HEAD" oder "log -3"
- finish(answer): beendet die Aufgabe mit der Antwort
"""


class Decision(BaseModel):
    thought: str
    tool: str
    args: dict = {}


def log(step: int, **data) -> None:
    rec = {"ts": round(time.time(), 3), "step": step, **data}
    with TRACE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def execute(d: Decision) -> str:
    fn = TOOLS.get(d.tool)
    if fn is None:
        return f"FEHLER: Unbekanntes Tool {d.tool!r}"
    try:
        return fn(**d.args)
    except Exception as e:
        return f"FEHLER: {type(e).__name__}: {e}"


def run(task: str) -> str:
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": task}]
    last_key, streak = "", 0
    for step in range(1, MAX_STEPS + 1):
        raw = ask_model(messages)          # entscheiden
        messages.append({"role": "assistant", "content": raw})
        try:
            d = Decision.model_validate_json(raw)
        except ValidationError as e:
            err = e.errors()[0]
            feld = ".".join(map(str, err["loc"])) or "Objekt"
            obs = (f"FEHLER in Ihrer Antwort, Feld {feld!r}: "
                   f"{err['msg']}")
            key = obs
        else:
            if d.tool == "finish":
                answer = str(d.args.get("answer", ""))
                log(step, tool="finish", answer=answer)
                return answer
            obs = execute(d)               # handeln
            key = f"{d.tool}|{sorted(d.args.items())}|{obs}"
        streak = streak + 1 if key == last_key else 1
        last_key = key
        if streak > MAX_REPEATS:
            log(step, abort="repeat", key=key[:200])
            return "ABBRUCH: Wiederholung ohne Fortschritt"
        log(step, raw=raw, observation=obs[:500],
            usage=dict(LAST_USAGE))
        messages.append(                   # beobachten
            {"role": "user", "content": f"OBSERVATION: {obs}"})
    log(MAX_STEPS, abort="step_budget")
    return "ABBRUCH: Step-Budget erschöpft"


if __name__ == "__main__":
    import sys
    print(run(" ".join(sys.argv[1:])))
