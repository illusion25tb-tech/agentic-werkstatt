"""Fortsetzbarkeit: Erledigtes läuft kein zweites Mal."""
from types import SimpleNamespace

import run_suite


def test_fortsetzen(tmp_path, monkeypatch):
    calls = []

    def fake(task, run, **kw):
        calls.append((task.id, run))
        return {"task": task.id, "run": run,
                "outcome": "falsch"}
    monkeypatch.setattr(run_suite, "run_one", fake)
    tasks = [SimpleNamespace(id="A"), SimpleNamespace(id="B")]
    res = tmp_path / "results.jsonl"
    assert run_suite.suite(tasks, 2, res) == 4
    assert calls == [("A", 1), ("B", 1), ("A", 2), ("B", 2)]
    assert run_suite.suite(tasks, 3, res) == 2   # nur Run 3
    assert len(res.read_text().splitlines()) == 6
