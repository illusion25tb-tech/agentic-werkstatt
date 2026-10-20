"""Ohne Modell: Jede Aufgabe auf dem Basisstand bewerten.
Erwartet: versteckte Tests rot, bestehende Tests grün."""
import json
import sys
import tempfile
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent / "solution"))

from grade import grade
from run_one import BUTLER, fresh_copy
from tasks import load_tasks

CODE = HIER.parents[1]
PY = str(CODE / "bestellservice/.venv/Scripts/python.exe")

with tempfile.TemporaryDirectory(
        ignore_cleanup_errors=True) as work:
    for t in load_tasks(CODE / "evals/tasks.json", CODE):
        repo = fresh_copy(
            CODE / "bestellservice", Path(work) / t.id,
            t.base_commit,
            BUTLER / "fixtures/AGENTS_bestellservice.md")
        g = grade(repo, t, PY)
        print(json.dumps({"task": t.id, **g}), flush=True)
