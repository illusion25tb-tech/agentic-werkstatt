"""Agent Loop mit nativem Function Calling."""
import json
import time
from pathlib import Path

from contracts import ToolError
from llm import LAST_USAGE, ask_model_tools
from tools import TOOLS

MAX_STEPS = 12
MAX_REPEATS = 2
TRACE = Path("trace.jsonl")
SYSTEM = ("Du bist ein Agent. Nutze die Tools. Wenn die "
          "Aufgabe gelöst ist, antworte ohne Tool Call.")


def log(step: int, **data) -> None:
    rec = {"ts": round(time.time(), 3), "step": step, **data}
    with TRACE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def run(task: str, toolbox=TOOLS) -> str:
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": task}]
    schemas = toolbox.schemas()
    last_key, streak = "", 0
    for step in range(1, MAX_STEPS + 1):
        reply = ask_model_tools(messages, schemas)
        messages.append(reply.message)
        if not reply.calls:                # fertig
            log(step, answer=reply.text, usage=dict(LAST_USAGE))
            return reply.text
        for call in reply.calls:
            try:
                obs = toolbox.call(call.name, call.args)
                kind = None
            except ToolError as e:
                obs, kind = str(e), e.kind
            log(step, tool_call_id=call.id, tool=call.name,
                args=call.args, thought=reply.text[:200],
                error=kind, observation=obs[:500],
                usage=dict(LAST_USAGE))
            messages.append({"role": "tool", "content": obs,
                             "tool_call_id": call.id})
        key = "|".join(f"{c.name}{c.args}" for c in reply.calls)
        key += obs
        streak = streak + 1 if key == last_key else 1
        last_key = key
        if streak > MAX_REPEATS:
            log(step, abort="repeat", key=key[:200])
            return "ABBRUCH: Wiederholung ohne Fortschritt"
    log(MAX_STEPS, abort="step_budget")
    return "ABBRUCH: Step-Budget erschöpft"


if __name__ == "__main__":
    import sys
    print(run(" ".join(sys.argv[1:])))
