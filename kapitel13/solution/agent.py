"""Agent Loop aus Kapitel 4, instrumentiert: Spans, Budget,
leere Observations als Fehler."""
import json
import os
import time
from pathlib import Path

from pydantic import BaseModel, ValidationError

from budget import BudgetExceeded, RunBudget
from llm import LAST_USAGE, ask_model  # aus Kapitel 3
from otel_spans import gen_ai_span, mark_error, set_attrs
from tools import TOOLS
from tools_guard import LEER, guard

MAX_STEPS = 12
MAX_REPEATS = 2
TRACE = Path("trace.jsonl")
MODEL = os.environ.get("LLM_MODEL", "unbekannt")
PROVIDER = os.environ.get("LLM_PROVIDER", "openai")

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
    except Exception as e:  # noqa: BLE001
        return f"FEHLER: {type(e).__name__}: {e}"


def decide(messages: list[dict], budget) -> str:
    if budget:
        budget.check_before(messages)      # vorher: Schätzung
    with gen_ai_span("chat", MODEL, model=MODEL,
                     provider=PROVIDER) as span:
        raw = ask_model(messages)
        set_attrs(span,
                  tokens_in=LAST_USAGE.get("prompt_tokens", 0),
                  tokens_out=LAST_USAGE.get(
                      "completion_tokens", 0))
    if budget:
        budget.add_usage(LAST_USAGE)       # nachher: exakt
    return raw


def act(d: Decision) -> str:
    with gen_ai_span("execute_tool", d.tool,
                     tool=d.tool) as span:
        obs = guard(execute(d))
        if obs.startswith("FEHLER"):
            kind = "empty" if obs == LEER else "tool_error"
            mark_error(span, kind, obs)
    return obs


def run(task: str, budget: RunBudget | None = None) -> str:
    with gen_ai_span("invoke_agent", "agent", agent="agent"):
        return _loop(task, budget)


def _loop(task: str, budget: RunBudget | None) -> str:
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": task}]
    last_key, streak = "", 0
    for step in range(1, MAX_STEPS + 1):
        try:
            raw = decide(messages, budget)  # entscheiden
        except BudgetExceeded as e:
            log(step, abort=e.reason, detail=e.detail)
            return f"ABBRUCH: {e.reason}"
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
            obs = act(d)                    # handeln
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
