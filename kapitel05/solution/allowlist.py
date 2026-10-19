"""Allowlist mit Fingerabdruck für MCP-Tools."""
import hashlib
import json
import sys
from pathlib import Path

PINS = Path("pins.json")


def fingerprint(tool) -> str:
    data = {"name": tool.name, "description": tool.description,
            "schema": tool.input_schema}
    text = json.dumps(data, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def check(tools: list, pins: dict) -> tuple[list, list]:
    ok, rejected = [], []
    for t in tools:
        if pins.get(t.name) == fingerprint(t):
            ok.append(t)
        else:
            grund = "geändert" if t.name in pins else "neu"
            rejected.append((t.name, grund))
    return ok, rejected


if __name__ == "__main__":       # python allowlist.py server.py
    from mcp_bridge import list_tools
    tools = list_tools(sys.argv[1])
    for t in tools:                  # erst lesen, dann pinnen
        print(f"--- {t.name}\n{t.description}")
        print(json.dumps(t.input_schema, ensure_ascii=False))
    pins = {t.name: fingerprint(t) for t in tools}
    PINS.write_text(json.dumps(pins, indent=1),
                    encoding="utf-8")
    print(f"{len(pins)} Tools in {PINS} festgeschrieben.")
