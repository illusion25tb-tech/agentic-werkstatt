"""Repo Map: Pfade und Top-Level-Symbole, gekürzt auf Budget."""
from pathlib import Path

from outline import outline
from search_rg import walk


def _rang(rel: str) -> int:
    """Kürzungsreihenfolge: höchster Rang fällt zuerst weg."""
    name = rel.rsplit("/", 1)[-1]
    if rel.startswith("tests/") or name.startswith("test_"):
        return 3
    if name in ("__init__.py", "conftest.py"):
        return 2                        # Hilfsmodule
    return 0 if name.endswith(".py") else 1


def _symbole(rel: str, root: Path) -> str:
    out = []
    for z in outline(rel, root).splitlines():
        if not z[0].isdigit():          # Methoden, Leerfall
            continue
        t = z.split()
        name = t[2] if t[1] in ("def", "class") else t[1]
        out.append(f"{name}:{t[0].split('-')[0]}")
    return ", ".join(out)


def repo_map(root: Path, budget: int = 3000) -> str:
    rows = []
    for f, rel in walk(root, root):
        sym = _symbole(rel, root) if f.suffix == ".py" else ""
        zeile = f"{rel} | {sym}" if sym else rel
        rows.append((_rang(rel), rel, zeile))
    rows.sort()
    out, used = [], 0
    for i, (_, _, zeile) in enumerate(rows):
        if used + len(zeile) + 1 > budget - 50:   # Platz
            out.append(f"... {len(rows) - i} Dateien "
                       "ausgelassen (Budget)")
            break
        out.append(zeile)
        used += len(zeile) + 1
    return "\n".join(out)
