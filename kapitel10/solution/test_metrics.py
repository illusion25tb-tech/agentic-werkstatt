"""Kennzahlen aus einem handgeschriebenen Trace."""
import json

from metrics import cost, load_prices, metrics

TRACE = [
    {"tool": "search", "args": {"pattern": "XL"},
     "obs": "bestellservice/versand.py:8: return"},
    {"tool": "read_file", "args": {"path": "nix.py"},
     "obs": "FEHLER: FileNotFoundError: nix.py"},
    {"tool": "read_file", "args": {"path": "nix.py"},
     "obs": "FEHLER: FileNotFoundError: nix.py"},
    {"tool": "read_file",
     "args": {"path": "bestellservice/versand.py"},
     "obs": "   1| ..."},
    {"phase": "plan", "requests": 4, "input_tokens": 9000,
     "output_tokens": 300},
    {"tool": "replace_in_file", "args": {"path": "t.py"},
     "obs": "FEHLER [policy]: Bestehender Test: tabu."},
    {"tool": "create_test", "args": {"path": "tests/t.py"},
     "obs": "tests/t.py: angelegt."},
    {"phase": "butler", "requests": 2, "input_tokens": 1000,
     "output_tokens": 200, "failed": ["..."]},
    {"abort": "UsageLimitExceeded: tool_calls_limit"}]


def test_metrics(tmp_path):
    p = tmp_path / "trace.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in TRACE))
    m = metrics(p, ["bestellservice/versand.py",
                    "bestellservice/tariffs.py"])
    assert (m["tool_calls"], m["errors"], m["repeats"]) == \
        (6, 3, 1)
    assert (m["asked"], m["policy"]) == (2, 1)
    assert (m["input_tokens"], m["output_tokens"]) == \
        (10000, 500)
    assert m["recall"] == 0.5
    assert m["abort"].startswith("UsageLimitExceeded")


def test_cost(tmp_path):
    p = tmp_path / "prices.toml"
    p.write_text('[models.m]\ninput = 2.0\noutput = 10.0\n')
    prices = load_prices(p)
    assert cost("m", 10000, 500, prices) == 0.025
    assert cost("unbekannt", 1, 1, prices) is None
