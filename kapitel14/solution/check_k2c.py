"""python check_k2c.py --root REPO CODE.py [FIXTURE ...]

Gates für den Knowledge-to-Code-Agenten: Jede Funktion im
erzeugten Code nennt ihre Dokumentstelle, und Fixtures
enthalten nur synthetische Personendaten."""
import argparse
import ast
import re
import sys
from pathlib import Path

QUELLE = re.compile(r"Quelle: (\S+\.md):(\d+)-(\d+)")
MAIL = re.compile(r"[\w.+-]+@([\w-]+(?:\.[\w-]+)+)")
NAME = re.compile(r'"name2?":\s*"([^"]*)"')
SYNTHETISCH = {"Erika Musterfrau", "Max Mustermann"}


def provenance(code: Path, root: Path) -> list[str]:
    out = []
    for f in ast.parse(code.read_text("utf-8")).body:
        if not isinstance(f, ast.FunctionDef):
            continue
        m = QUELLE.search(ast.get_docstring(f) or "")
        if not m:
            out.append(f"{f.name}: keine Quelle")
            continue
        doc, a, b = root / m[1], int(m[2]), int(m[3])
        n = len(doc.read_text("utf-8").splitlines()) \
            if doc.is_file() else 0
        if not 1 <= a <= b <= n:
            out.append(f"{f.name}: {m[0]} gibt es nicht")
    return out


def personal_data(fixture: Path) -> list[str]:
    text = fixture.read_text("utf-8")
    mails = [m[0] for m in MAIL.finditer(text) if not m[1]
             .endswith(("example", "example.com",
                        "example.org", "example.net"))]
    names = [n for n in NAME.findall(text)
             if n not in SYNTHETISCH]
    return [f"{fixture.name}: {x}" for x in mails + names]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("code", type=Path)
    ap.add_argument("fixtures", type=Path, nargs="*")
    a = ap.parse_args(argv)
    found = provenance(a.code, a.root)
    for fx in a.fixtures:
        found += personal_data(fx)
    for f in found:
        print("ROT:", f)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
