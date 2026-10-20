"""python snapshots.py snapshots.yaml [md-ordner]

Meldet Einträge im Snapshot-Register, deren nächste Prüfung
fällig ist (Exit 1). Mit Ordner: listet zusätzlich alle
SNAPSHOT-Kästen der Markdown-Dateien mit den Daten darin."""
import re
import sys
from datetime import date
from pathlib import Path

import yaml

BOX = re.compile(r'<div class="box-title">SNAPSHOT: ([^<]*)'
                 r"</div>(.*?)</div>", re.DOTALL)
DATUM = re.compile(r"\b\d{1,2}\.\d{1,2}\.\d{4}\b")


def boxes(folder: Path) -> list[tuple[str, int, str, list]]:
    """(Datei, Zeile, Titel, Daten) je SNAPSHOT-Kasten."""
    out = []
    for md in sorted(folder.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        for m in BOX.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            dates = DATUM.findall(m.group(2))
            out.append((md.name, line, m.group(1), dates))
    return out


def due(register: Path, today: date) -> list[str]:
    data = yaml.safe_load(register.read_text(encoding="utf-8"))
    return [f"FÄLLIG seit {e['next']}: Kap. {e['chapter']},"
            f" {e['claim']}" for e in data["snapshots"]
            if e["next"] <= today]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) > 2:
        for name, line, title, dates in boxes(Path(sys.argv[2])):
            print(f"{name}:{line} {title} | {', '.join(dates)}")
    found = due(Path(sys.argv[1]), date.today())
    for f in found:
        print(f)
    sys.exit(1 if found else 0)
