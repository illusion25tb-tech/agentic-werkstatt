"""Fixture-Trace im Format von Kapitel 12: Testdaten."""
from replay import replay

TRACE = [
    {"role": "planner", "round": 0, "ts": 100.0,
     "tool": "read_file", "args": {}, "obs": "1: x"},
    {"role": "planner", "round": 0, "ts": 101.0,
     "tool": "search", "args": {}, "obs": "FEHLER [x]: y"},
    {"role": "planner", "round": 0, "ts": 110.0,
     "phase": "work",
     "requests": 2, "input_tokens": 1800, "output_tokens": 400},
    {"role": "orchestrator", "ts": 110.5, "plan": ["a.py"]},
    {"role": "coder", "round": 1, "ts": 130.0, "phase": "work",
     "requests": 1, "input_tokens": 900, "output_tokens": 300},
    {"role": "tester", "round": 1, "ts": 140.0, "green": True},
    {"role": "orchestrator", "ts": 141.0, "abort": "Stop: x"},
]


def test_hierarchie_aus_flachem_trace(spans):
    replay(TRACE, "m")
    s = {x.name: x for x in spans()}
    wf = s["invoke_workflow release-engineer"]
    planner = s["invoke_agent planner"]
    assert planner.parent.span_id == wf.context.span_id
    assert s["chat m"].parent.span_id in {
        x.context.span_id for x in spans()
        if x.name.startswith("invoke_agent")}
    assert not s["execute_tool search"].status.is_ok
    assert wf.attributes["werkstatt.abort"] == "Stop: x"
    assert (wf.end_time - wf.start_time) == 41 * 10**9
    names = [x.name for x in spans()]
    assert "invoke_agent tester" not in names


def test_token_je_rolle(spans):
    replay(TRACE, "m")
    tokens = {}
    by_id = {x.context.span_id: x for x in spans()}
    for x in spans():
        if x.name == "chat m":
            rolle = by_id[x.parent.span_id].attributes[
                "gen_ai.agent.name"]
            tokens[rolle] = (
                x.attributes["gen_ai.usage.input_tokens"]
                + x.attributes["gen_ai.usage.output_tokens"])
    assert tokens == {"planner": 2200, "coder": 1200}
