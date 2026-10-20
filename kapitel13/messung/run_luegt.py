"""Break-Messung: read_file liefert beim ersten Aufruf "".

python run_luegt.py <runs>   (LLM_* wie in Kapitel 3 setzen)

Der Guard aus tools_guard.py ist für diese Messung AUS: Es
geht darum, wie das Modell auf den nackten leeren String
reagiert. Trace je Run unter luegt/run_N/, Spans aller Runs
in luegt/spans.jsonl (je Run eine eigene Trace-ID)."""
import json
import os
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
SOLUTION = HIER.parent / "solution"
os.chdir(SOLUTION)                   # workspace/ liegt dort
sys.path.insert(0, str(SOLUTION))

from opentelemetry.sdk.trace.export import (
    ConsoleSpanExporter,
)

import agent
import tools
from otel_spans import setup

TASK = "Wie hoch ist der Gesamtwert von bestellungen/4711.json?"


def luegt(fn):
    calls = {"n": 0}

    def wrapper(**kw):
        calls["n"] += 1
        return "" if calls["n"] == 1 else fn(**kw)
    return wrapper


def main(runs: int) -> None:
    root = HIER / "luegt"
    root.mkdir(exist_ok=True)
    spans = root / "spans.jsonl"
    with spans.open("w", encoding="utf-8") as f:
        setup(ConsoleSpanExporter(
            out=f, formatter=lambda s: s.to_json(indent=None)
            + "\n"))
        agent.guard = str            # Guard aus (Break)
        for i in range(1, runs + 1):
            d = root / f"run_{i}"
            d.mkdir(exist_ok=True)
            agent.TRACE = d / "trace.jsonl"
            agent.TRACE.unlink(missing_ok=True)
            agent.TOOLS["read_file"] = luegt(tools.read_file)
            answer = agent.run(TASK)
            print(json.dumps({"run": i, "answer": answer},
                             ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 3)
