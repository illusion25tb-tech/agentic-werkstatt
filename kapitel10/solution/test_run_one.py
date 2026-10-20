"""run_one mit geskriptetem Modell (FunctionModel)."""
import json
import sys

from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import (
    ModelResponse,
    TextPart,
    ToolCallPart,
)
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.usage import UsageLimits

from run_one import agent, run_one  # agent: Kap. 9

V = "bestellservice/versand.py"
PLAN = json.dumps({
    "files": [{"path": V, "why": "return XL"}],
    "change": "Über 31,5 kg SPERRGUT", "new_tests": [],
    "risks": []})
REPORT = json.dumps({
    "summary": "Sperrgut über 31,5 kg", "changed_files": [V],
    "reasons": [{"text": "Rückfall ist jetzt Sperrgut",
                 "path": V, "line_start": 8, "line_end": 8,
                 "quote": 'return "SPERRGUT"'}],
    "tests": "grün", "risks": []})
PRICES = {"models": {"skript": {"input": 2.0, "output": 10.0}}}


def skript(*schritte):
    it = iter(schritte)

    def antwort(messages, info) -> ModelResponse:
        s = next(it, None)
        if s is None:
            raise UnexpectedModelBehavior("Skript zu Ende")
        if isinstance(s, Exception):
            raise s
        part = TextPart(s) if isinstance(s, str) \
            else ToolCallPart(*s)
        return ModelResponse(parts=[part])
    return FunctionModel(antwort)


def run(task, source, tmp_path, model):
    return run_one(task, 1, source=source,
                   work=tmp_path / "work", out=tmp_path / "out",
                   model=model, model_name="skript",
                   python=sys.executable, prices=PRICES,
                   agents_md=None)


def test_geloest(task, source, tmp_path):
    rec = run(task, source, tmp_path, skript(
        ("read_file", {"path": V}), "Ursache: Zeile 8.", PLAN,
        ("replace_in_file", {"path": V,
                             "old": '    return "XL"\n',
                             "new": '    return "SPERRGUT"\n'}),
        ("run_tests", {"target": "tests"}), "Fertig.", REPORT))
    assert (rec["exit"], rec["outcome"]) == (0, "gelöst")
    assert rec["resolved"] and rec["recall"] == 1.0
    assert (rec["tool_calls"], rec["asked"]) == (3, 1)
    assert rec["cost"] > 0 and not rec["over_budget"]
    assert len(rec["prompt"]) == len(rec["harness"]) == 12
    assert not (tmp_path / "work/NL-900_1").exists()
    out = tmp_path / "out/NL-900/run_1"
    assert "SPERRGUT" in (out / "diff.patch").read_text()


def test_budget_ist_kein_absturz(task, source, tmp_path,
                                 monkeypatch):
    monkeypatch.setattr(agent, "LIMITS",
                        UsageLimits(tool_calls_limit=2))
    lesen = ("read_file", {"path": V})
    rec = run(task, source, tmp_path,
              skript(lesen, lesen, lesen, lesen))
    assert (rec["exit"], rec["outcome"]) == (2, "budget")
    assert rec["input_tokens"] > 0       # auch bei Abbruch


def test_absturz_wird_verbucht(task, source, tmp_path):
    rec = run(task, source, tmp_path,
              skript(RuntimeError("Netz weg")))
    assert rec["exit"] is None and rec["outcome"] == "absturz"
    assert "Netz weg" in rec["crash"]
