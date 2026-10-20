"""Explorer ohne Modell: Tools direkt, Agent mit Skript."""
import pytest
from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.models.function import FunctionModel

import agent
from deps import Deps
from tools_read import list_files, read_file, search

V = "bestellservice/versand.py"


@pytest.fixture
def deps(tmp_path):
    repo = tmp_path / "repo"
    (repo / "bestellservice").mkdir(parents=True)
    (repo / V).write_bytes(b'def klasse(kg):\n'
                           b'    return "XL"\n')
    return Deps(repo, tmp_path / "trace.jsonl")


def test_tools_lesen_mit_zeilen_und_grenze(deps):
    assert V in list_files(deps)
    assert '   2|     return "XL"' in read_file(deps, V)
    assert f"{V}:2:" in search(deps, "return")
    with pytest.raises(PermissionError):
        read_file(deps, "../geheim.txt")


def test_plan_mit_erfundener_datei_geht_zurueck(deps):
    falsch = {"files": [{"path": "porto.py", "why": "?"}],
              "change": "-", "new_tests": [], "risks": []}
    richtig = dict(falsch, files=[{"path": V, "why": "XL"}])
    it = iter([("read_file", {"path": V}),
               ("final_result", falsch),
               ("final_result", richtig)])
    model = FunctionModel(lambda m, info: ModelResponse(
        parts=[ToolCallPart(*next(it))]))
    plan = agent.make_plan("38 kg: falscher Tarif", deps, model)
    assert plan.files[0].path == V
    assert "read_file" in deps.trace.read_text("utf-8")
