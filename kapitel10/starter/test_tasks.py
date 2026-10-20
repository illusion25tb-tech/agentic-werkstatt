"""Das echte Golden Task Set ist vollständig und getrennt."""
import json
from pathlib import Path

import pytest

from tasks import load_tasks

CODE = Path(__file__).resolve().parents[2]


def test_golden_tasks_vollstaendig():
    tasks = load_tasks(CODE / "evals/tasks.json", CODE)
    assert [t.id for t in tasks] == [
        f"NL-{n}" for n in range(111, 121)]
    service = (CODE / "bestellservice").resolve()
    for t in tasks:
        assert t.issue.is_file()
        for h in t.hidden_tests:
            assert h.is_file()
            assert not h.resolve().is_relative_to(service)
    assert sum(t.ambiguous for t in tasks) == 2


def test_fehlendes_feld(tmp_path):
    p = tmp_path / "tasks.json"
    p.write_text(json.dumps({"tasks": [{"id": "X"}]}))
    with pytest.raises(ValueError, match="fehlt"):
        load_tasks(p, tmp_path)
