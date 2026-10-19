"""Suche mit Zeilenbelegen: ripgrep, sonst reines Python."""
import json
import re
import shutil
import subprocess
from pathlib import Path

from contracts import ToolError
from read_lines import im_repo

MAX_HITS = 30
SKIP = {"__pycache__", "node_modules"}  # dazu alles mit "."


def search(pattern: str, path: str, root: Path) -> str:
    base = im_repo(path, root)
    rel = base.relative_to(root).as_posix()
    if shutil.which("rg"):
        hits = _rg(pattern, rel, root)
    else:                       # Fallback, gleiche Ausgabe
        hits = _py(pattern, base, root)
    if not hits:
        return f"Keine Treffer für {pattern!r} in {rel}."
    hits.sort()
    out = [f"{p}:{n}: {t.strip()[:100]}"
           for p, n, t in hits[:MAX_HITS]]
    if len(hits) > MAX_HITS:
        out.append(f"... {len(hits)} Treffer, gekürzt auf "
                   f"{MAX_HITS}. Suche enger fassen.")
    return "\n".join(out)


def _rg(pattern: str, rel: str, root: Path) -> list:
    proc = subprocess.run(
        ["rg", "--json", "-i", "-e", pattern, rel],
        cwd=root, capture_output=True, text=True,
        encoding="utf-8", timeout=10, check=False)
    if proc.returncode == 2:    # 1 heißt nur: kein Treffer
        raise ToolError("invalid_args", proc.stderr[:300])
    return parse_rg(proc.stdout)


def parse_rg(stdout: str) -> list:
    hits = []
    for line in stdout.splitlines():
        msg = json.loads(line)
        if msg["type"] != "match":
            continue            # begin, end, context, summary
        d = msg["data"]
        if "text" not in d["path"] or "text" not in d["lines"]:
            continue            # Binärinhalt kommt als bytes
        path = d["path"]["text"].replace("\\", "/")
        path = path.removeprefix("./")  # bei Suche in "."
        text = d["lines"]["text"].splitlines()[0]
        hits.append((path, d["line_number"], text))
    return hits


def _py(pattern: str, base: Path, root: Path) -> list:
    # Grenze: kennt .gitignore nicht, nur SKIP und Punkt-Ordner
    try:
        rx = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        raise ToolError("invalid_args", f"Regex: {e}") from None
    hits = []
    for f, rel in walk(base, root):
        text = f.read_text(encoding="utf-8", errors="ignore")
        for n, line in enumerate(text.splitlines(), 1):
            if rx.search(line):
                hits.append((rel, n, line))
    return hits


def walk(base: Path, root: Path):
    """Dateien unter base mit relativem Pfad, sortiert."""
    files = [base] if base.is_file() else base.rglob("*")
    for f in sorted(files):
        parts = f.relative_to(root).parts
        if f.is_file() and not any(
                p in SKIP or p.startswith(".") for p in parts):
            yield f, "/".join(parts)
