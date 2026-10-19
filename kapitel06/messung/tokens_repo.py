"""Tokenzahl des bestellservice, gemessen über Ollama.

Je Datei ein Aufruf von /api/generate (raw, num_predict 1),
gezählt wird prompt_eval_count. Davon abgezogen: der Wert für
den Präfix allein. Aufruf: python tokens_repo.py llama3.2:3b
"""
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parents[2] / "bestellservice"
MODEL = sys.argv[1] if len(sys.argv) > 1 else "llama3.2:3b"


def count(text: str) -> int:
    body = {"model": MODEL, "prompt": text, "raw": True,
            "stream": False,
            "options": {"num_predict": 1, "num_ctx": 8192}}
    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())["prompt_eval_count"]


basis = count("# 0\n")
gruppen = {"code": [], "tests": [], "doku": []}
for f in sorted(ROOT.rglob("*")):
    rel = f.relative_to(ROOT).as_posix()
    if not f.is_file() or any(p.startswith(".") or
                              p == "__pycache__"
                              for p in f.relative_to(ROOT).parts):
        continue
    if f.suffix == ".py":
        g = "tests" if rel.startswith("tests/") else "code"
    elif f.suffix == ".md":
        g = "doku"
    else:
        continue
    text = f.read_text(encoding="utf-8")
    n = count(f"# {len(gruppen[g])+1}\n" + text) - basis
    gruppen[g].append((rel, len(text.splitlines()), len(text), n))

erg = {"model": MODEL, "basis_prefix": basis}
for g, rows in gruppen.items():
    erg[g] = {"dateien": len(rows),
              "zeilen": sum(r[1] for r in rows),
              "zeichen": sum(r[2] for r in rows),
              "tokens": sum(r[3] for r in rows)}
erg["details"] = gruppen
print(json.dumps({k: v for k, v in erg.items() if k != "details"},
                 ensure_ascii=False, indent=1))
Path(__file__).with_name("tokens_repo.json").write_text(
    json.dumps(erg, ensure_ascii=False, indent=1),
    encoding="utf-8")
