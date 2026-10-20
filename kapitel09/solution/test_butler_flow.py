"""Ganzer Ablauf mit geskriptetem Modell (FunctionModel)."""
import json
import sys

from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import (
    ModelResponse,
    TextPart,
    ToolCallPart,
)
from pydantic_ai.models.function import FunctionModel

import cli
import git_ops

V = "bestellservice/versand.py"

PLAN = json.dumps({
    "files": [{"path": V, "why": "return XL"}],
    "change": "Über 31,5 kg SPERRGUT statt XL",
    "new_tests": ["38 kg ist SPERRGUT"], "risks": []})
NEU = ("from bestellservice.versand import klasse\n\n\n"
       "def test_grenze_bleibt_xl():\n"
       '    assert klasse(31.5) == "XL"\n')
REPORT = json.dumps({
    "summary": "Sperrgut über 31,5 kg",
    "changed_files": [V],
    "reasons": [{"text": "Rückfall ist jetzt Sperrgut",
                 "path": V, "line_start": 8, "line_end": 8,
                 "quote": 'return "SPERRGUT"'}],
    "tests": "Suite grün", "risks": []})


def skript(*schritte):
    """Tool Calls als Tupel, Text als str, der Reihe nach."""
    it = iter(schritte)

    def antwort(messages, info) -> ModelResponse:
        s = next(it, None)
        if s is None:
            raise UnexpectedModelBehavior("Skript zu Ende")
        part = TextPart(s) if isinstance(s, str) \
            else ToolCallPart(*s)
        return ModelResponse(parts=[part])
    return FunctionModel(antwort)


def butler(repo, tmp_path, model, antworten):
    issue = tmp_path / "NL-107.md"
    issue.write_text("Label 38 kg hat Standardtarif.")
    fragen = []

    def approve(risk, tool, args):
        fragen.append(str(risk))
        return antworten.pop(0)
    code = cli.main([str(issue), "--repo", str(repo),
                     "--python", sys.executable,
                     "--out", str(tmp_path)], approve, model)
    return code, fragen


def test_lesen_plan_freigabe_aenderung_report(repo, tmp_path):
    model = skript(
        ("read_file", {"path": V}),
        "Ursache: Rückfall auf XL in Zeile 8.",   # Explorer
        PLAN,                                     # Form
        ("replace_in_file", {"path": V,
                             "old": '    return "XL"\n',
                             "new": '    return "SPERRGUT"\n'}),
        ("create_test", {"path": "tests/test_grenze.py",
                         "content": NEU}),
        ("run_tests", {"target": "tests"}),
        "Fertig, Suite grün.",                    # Worker
        REPORT)                                   # Form
    code, fragen = butler(repo, tmp_path, model, [True] * 4)
    assert code == 0
    assert fragen == ["plan", "schreiben", "schreiben",
                      "commit"]
    log = git_ops.git(repo, "log", "--oneline", "-1")
    assert "NL-107: Sperrgut" in log
    assert "versand.py:8-8" in (tmp_path / "pr_NL-107.md"
                                ).read_text("utf-8")


def test_butler_der_den_test_repariert(repo, tmp_path):
    """Praxis-Box, nachgestellt: Statt den Code zu ändern,
    greift das Modell nach den Tests."""
    model = skript(
        "Plan steht.", PLAN,
        ("replace_in_file", {
            "path": "tests/test_acceptance_x.py",
            "old": '"SPERRGUT"', "new": '"XL"'}),
        ("replace_in_file", {
            "path": "tests/test_versand.py",
            "old": '"S"', "new": '"XL"'}))
    code, fragen = butler(repo, tmp_path, model,
                          [True, True, False])
    assert code == 2                 # Skript zu Ende: Abbruch
    assert fragen == ["plan", "testdatei", "testdatei"]
    trace = (tmp_path / "trace_NL-107.jsonl").read_text("utf-8")
    assert "ist gesperrt (Acceptance Test)" in trace
    assert "testdatei: vom Menschen abgelehnt" in trace
    assert git_ops.git(repo, "diff", "HEAD") == ""


def test_fertig_ohne_gruen_geht_an_den_menschen(repo,
                                               tmp_path):
    model = skript("Plan steht.", PLAN, "Erledigt!")
    code, _ = butler(repo, tmp_path, model, [True])
    assert code == 2
    trace = (tmp_path / "trace_NL-107.jsonl").read_text("utf-8")
    assert "ohne grüne Suite" in trace


def test_plan_abgelehnt_nichts_geaendert(repo, tmp_path):
    model = skript("Plan steht.", PLAN)
    code, fragen = butler(repo, tmp_path, model, [False])
    assert code == 1 and fragen == ["plan"]
    assert git_ops.git(repo, "status", "--porcelain") == ""
    assert git_ops.git(repo, "branch") == "* main\n"


def test_schreibende_tools_laufen_nie_parallel():
    import agent
    from tools_read import read_file
    from tools_write import create_test
    assert agent.guarded(create_test).sequential
    assert not agent.guarded(read_file).sequential
