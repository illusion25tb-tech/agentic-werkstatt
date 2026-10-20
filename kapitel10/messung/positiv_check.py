"""Ohne Modell: Zwei Fixes von Hand, dann bewerten.
Prüft, dass grade() eine richtige Lösung auch erkennt."""
import json
import sys
import tempfile
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent / "solution"))

from grade import grade
from run_one import fresh_copy
from tasks import load_tasks

CODE = HIER.parents[1]
PY = str(CODE / "bestellservice/.venv/Scripts/python.exe")
FIX = {
    "NL-111": ("bestellservice/cart.py",
               ('    """Hinterlegt einen Gutscheincode am '
               'Warenkorb."""\n'),
               ('    """Hinterlegt einen Gutscheincode am '
               'Warenkorb."""\n    code = code.strip().upper()\n')),
    "NL-118": ("bestellservice/catalog.py",
               "quantity > article.bulk_from",
               "quantity >= article.bulk_from")}

with tempfile.TemporaryDirectory(
        ignore_cleanup_errors=True) as work:
    for t in load_tasks(CODE / "evals/tasks.json", CODE):
        if t.id not in FIX:
            continue
        repo = fresh_copy(CODE / "bestellservice",
                          Path(work) / t.id, t.base_commit, None)
        path, old, new = FIX[t.id]
        f = repo / path
        text = f.read_bytes().decode("utf-8")
        crlf = "\r\n" in text
        text = text.replace("\r\n", "\n")
        assert text.count(old) == 1, t.id
        text = text.replace(old, new)
        if crlf:
            text = text.replace("\n", "\r\n")
        f.write_bytes(text.encode("utf-8"))
        print(json.dumps({"task": t.id, **grade(repo, t, PY)}))
