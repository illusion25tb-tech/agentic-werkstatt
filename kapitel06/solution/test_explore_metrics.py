import json

from explore_metrics import metrics

TRACE = [
    {"step": 1, "tool": "search", "error": None,
     "args": {"pattern": "porto", "path": "."},
     "observation": "README.md:47: | `bestellservice/porto.py`"
     },
    {"step": 2, "tool": "read_lines", "error": "not_found",
     "args": {"path": "bestellservice/porto.py",
              "start": 1, "end": 40}, "observation": "FEHLER"},
    {"step": 3, "tool": "read_lines", "error": None,
     "args": {"path": "README.md", "start": 30, "end": 50},
     "observation": "..."},
    {"step": 4, "tool": "search", "error": None,
     "args": {"pattern": "def shipping_cost"},
     "observation": "bestellservice/shipping_costs.py:18: ..."},
    {"step": 5, "tool": "read_lines", "error": None,
     "args": {"path": "./bestellservice/shipping_costs.py",
              "start": 15, "end": 30}, "observation": "..."},
    {"step": 6, "answer": "{...}", "rejected": []},
]


def test_kennzahlen(tmp_path):
    t = tmp_path / "trace.jsonl"
    t.write_text("\n".join(json.dumps(r) for r in TRACE),
                 encoding="utf-8")
    m = metrics(t, {"bestellservice/shipping_costs.py"})
    assert m == {"recall": 1.0, "unnoetig": ["README.md"],
                 "calls_bis_treffer": 4, "calls": 5}


def test_frage_ohne_relevante_datei(tmp_path):
    t = tmp_path / "trace.jsonl"
    t.write_text(json.dumps(TRACE[0]), encoding="utf-8")
    assert metrics(t, set())["recall"] is None
