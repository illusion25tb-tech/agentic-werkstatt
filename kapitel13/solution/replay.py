"""python replay.py trace.jsonl spans.jsonl [modell]

Macht aus einem Trace des Orchestrators (Kapitel 12) Spans:
Workflow -> Agent je Rolle und Runde -> Modell und Tool."""
import json
import sys
from itertools import groupby
from pathlib import Path

from opentelemetry import trace
from opentelemetry.sdk.trace.export import ConsoleSpanExporter

from otel_spans import ATTR, mark_error, setup

AGENTS = {"planner", "coder", "reviewer"}  # Tester = pytest


def ns(rec: dict) -> int:
    return int(rec["ts"] * 1e9)      # Sekunden -> Nanosek.


def start(parent, op: str, name: str, t0: int, **attrs):
    """Span mit Startzeit aus dem Trace statt 'jetzt'."""
    a = {ATTR["op"]: op}
    a |= {ATTR[k]: v for k, v in attrs.items()}
    ctx = trace.set_span_in_context(parent) if parent else None
    return trace.get_tracer("agentic-werkstatt").start_span(
        f"{op} {name}", context=ctx, attributes=a,
        start_time=t0)


def replay(recs: list[dict], model: str,
           workflow: str = "release-engineer") -> None:
    t = ns(recs[0])                  # Ende des letzten Eintrags
    wf = start(None, "invoke_workflow", workflow, t,
               workflow=workflow)
    for (role, rnd), grp in groupby(
            recs, lambda r: (r.get("role"), r.get("round"))):
        grp = list(grp)
        for r in grp:
            if "abort" in r:
                wf.set_attribute("werkstatt.abort", r["abort"])
        if role not in AGENTS:
            t = ns(grp[-1])
            continue
        ag = start(wf, "invoke_agent", role, t, agent=role)
        ag.set_attribute("werkstatt.round", rnd)
        for r in grp:
            if "tool" in r:       # Dauer unbekannt: Zeitpunkt
                s = start(ag, "execute_tool", r["tool"], ns(r),
                          tool=r["tool"])
                obs = r["obs"]
                if obs.startswith("FEHLER") or not obs.strip():
                    mark_error(s, "tool_error", obs)
                s.end(end_time=ns(r))
            elif "phase" in r:       # Summe einer Phase
                s = start(ag, "chat", model, t, model=model,
                          tokens_in=r["input_tokens"],
                          tokens_out=r["output_tokens"])
                s.set_attribute("werkstatt.requests",
                                r["requests"])
                s.end(end_time=ns(r))
            t = ns(r)
        ag.end(end_time=ns(grp[-1]))
    wf.end(end_time=ns(recs[-1]))


if __name__ == "__main__":
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    model = sys.argv[3] if len(sys.argv) > 3 else "llama3.2-16k"
    with dst.open("w", encoding="utf-8") as out:
        setup(ConsoleSpanExporter(
            out=out, formatter=lambda s: s.to_json(indent=None)
            + "\n"))
        replay([json.loads(z) for z in src.read_text(
            encoding="utf-8").splitlines()], model)
