import json

from pydantic import BaseModel

import agent_fc
import plan_mode
from contracts import Registry, ToolSpec
from llm import Reply, ToolCall
from tools import GROUNDING, ROOT

SCOPE = ["bestellservice/orders.py", "bestellservice/api.py"]
PLAN = {"goal": "NL-105", "steps": [
    {"id": "s1", "goal": "Status cancelled",
     "files": ["bestellservice/orders.py"],
     "check": "pytest tests/test_orders.py"}]}


class Leer(BaseModel):
    pass


def test_nur_lesende_tools():
    schreiben = ToolSpec("write_file", "schreibt", Leer,
                         lambda: "ok", read_only=False)
    voll = Registry([*GROUNDING.specs.values(), schreiben])
    assert "write_file" not in plan_mode.read_only(voll).specs
    assert len(plan_mode.read_only(voll).specs) == 3


def test_check_lehnt_scope_und_beispielpfad_ab(tmp_path):
    raw = json.dumps({"goal": "x", "steps": [
        {"id": "s1", "goal": "y", "check": "pytest",
         "files": ["bestellservice/labels.py",
                   "pfad/zur/datei.py"]}]})
    fehler = plan_mode.check(raw, ROOT, SCOPE)
    assert "s1: pfad/zur/datei.py gibt es nicht" in fehler
    assert ("s1: bestellservice/labels.py liegt außerhalb "
            "des Scopes") in fehler


def test_markdown_statt_json():
    # Gestalt aus einem echten Run (messung/traces/plan_0)
    raw = ("Hier ist der Plan:\n1. **S6** GET "
           "/orders/{id}/history")
    assert plan_mode.check(raw, ROOT, SCOPE)[0].startswith(
        "Kein JSON: Antworte nur mit dem Plan")


def test_plan_mode_speichert_plan(monkeypatch, tmp_path):
    monkeypatch.setattr(agent_fc, "TRACE", tmp_path / "t.jsonl")
    monkeypatch.setattr(plan_mode, "PLAN_FILE",
                        tmp_path / "plan.json")
    antworten = iter([
        Reply("", [ToolCall("c1", "write_file",
                            {"path": "x.py"})], {}),
        Reply(json.dumps(PLAN), [], {})])
    gesehen = []

    def fake(messages, tools):
        gesehen.append([t["function"]["name"] for t in tools])
        return next(antworten)
    monkeypatch.setattr(agent_fc, "ask_model_tools", fake)
    p = plan_mode.make_plan("Spezifikation", SCOPE)
    assert gesehen[0] == ["search", "read_lines", "outline"]
    trace = (tmp_path / "t.jsonl").read_text(encoding="utf-8")
    assert "unknown_tool" in trace
    assert p.steps[0].id == "s1"
    gespeichert = json.loads((tmp_path / "plan.json").read_text(
        encoding="utf-8"))
    assert gespeichert["steps"][0]["depends_on"] == []
