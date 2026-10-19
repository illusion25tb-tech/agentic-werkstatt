"""Zählt die Traces aus run_vergleich.py aus.

Formfehler = Schritt, dessen Aufruf wegen Format oder Argumenten
gar nicht beim Werkzeug ankam (JSON-Text: ungültige Antwort oder
TypeError/AttributeError aus
falscher Argumentform, unbekanntes Tool; Function Calling: invalid_args oder unknown_tool).
"""
import json
import re
from collections import defaultdict
from pathlib import Path

HIER = Path(__file__).parent
RICHTIG = re.compile(r"12[.,]5|204[.,]8.*217[.,]3")
runs = [json.loads(z) for z in
        (HIER / "ergebnisse.jsonl").read_text(
            encoding="utf-8").splitlines()]
tab = defaultdict(lambda: defaultdict(int))
for r in runs:
    if not r["variant"] in ("json_text", "fc"):
        continue
    k = (r["variant"], r["task"], r["model"])
    tr = HIER / "traces" / (
        f"{r['variant']}_{r['task']}_"
        f"{r['model'].replace(':', '_')}_{r['run']}.jsonl")
    t = tab[k]
    t["runs"] += 1
    t["richtig"] += bool(RICHTIG.search(r["answer"]))
    t["abbruch"] += r["answer"].startswith("ABBRUCH")
    for z in tr.read_text(encoding="utf-8").splitlines():
        s = json.loads(z)
        if "abort" in s or "answer" in s:
            continue
        t["aufrufe"] += 1
        obs = s.get("observation", "")
        if r["variant"] == "json_text":
            form = (obs.startswith("FEHLER in Ihrer Antwort")
                    or obs.startswith("FEHLER: Unbekanntes Tool")
                    or "TypeError" in obs
                    or "AttributeError" in obs)
        else:
            form = s.get("error") in ("invalid_args",
                                      "unknown_tool")
        t["formfehler"] += form
for k, t in sorted(tab.items()):
    print(k, dict(t))
