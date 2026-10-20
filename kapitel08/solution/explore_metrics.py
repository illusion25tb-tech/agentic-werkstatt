"""Exploration messen, unabhängig von der Antwort."""
import json
from pathlib import Path

LESEND = {"read_lines", "read_file", "outline"}


def _norm(p: str) -> str:
    return p.replace("\\", "/").removeprefix("./")


def metrics(trace: Path, relevant: set[str]) -> dict:
    gelesen, erster, nr = set(), None, 0
    for line in trace.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        if "tool" not in rec:
            continue                    # Antwort oder Abbruch
        nr += 1
        args = rec["args"]
        if not isinstance(args, dict):  # kaputtes JSON
            args = {}
        pfad = _norm(str(args.get("path", "")))
        if rec["tool"] in LESEND and not rec.get("error"):
            gelesen.add(pfad)
        fund = pfad in relevant or any(
            r in rec.get("observation", "") for r in relevant)
        if erster is None and fund:
            erster = nr
    treffer = len(gelesen & relevant)
    return {"recall": treffer / len(relevant) if relevant
            else None,
            "unnoetig": sorted(gelesen - relevant),
            "calls_bis_treffer": erster, "calls": nr}
