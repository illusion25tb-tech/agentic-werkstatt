"""Kennzahlen eines Runs, berechnet aus trace.jsonl."""
import json
import tomllib
from pathlib import Path

WRITE = {"replace_in_file", "create_test"}  # wie policy.RISK


def load_prices(path: Path) -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def cost(model: str, tin: int, tout: int, prices: dict):
    p = prices["models"].get(model)
    if p is None:
        return None      # unbekannt ist nicht dasselbe wie 0
    return (tin * p["input"] + tout * p["output"]) / 1e6


def metrics(trace: Path, expected: list[str]) -> dict:
    m = {"tool_calls": 0, "errors": 0, "repeats": 0,
         "asked": 0, "policy": 0, "input_tokens": 0,
         "output_tokens": 0, "abort": None}
    read, last = set(), None
    for line in trace.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        m["input_tokens"] += r.get("input_tokens", 0)
        m["output_tokens"] += r.get("output_tokens", 0)
        m["abort"] = r.get("abort", m["abort"])
        if "tool" not in r:
            continue                 # Phase, Abbruch, Report
        obs, args = r["obs"], r["args"]
        ok = not obs.startswith("FEHLER")
        m["tool_calls"] += 1
        m["errors"] += not ok
        m["policy"] += obs.startswith("FEHLER [policy]")
        m["asked"] += r["tool"] in WRITE   # Eval: gezählt
        key = (r["tool"], json.dumps(args, sort_keys=True), obs)
        m["repeats"] += key == last
        last = key
        if r["tool"] == "read_file" and ok:
            path = str(args.get("path", ""))
            read.add(path.replace("\\", "/"))
    hit = read & set(expected)
    m["recall"] = len(hit) / len(expected) if expected else None
    m["files_read"] = sorted(read)
    return m
