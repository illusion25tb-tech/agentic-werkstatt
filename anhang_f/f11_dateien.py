"""Dateien und Pfade mit pathlib und with."""

import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    folder = Path(tmp) / "issues"
    folder.mkdir()
    ticket = folder / "NL-102.md"
    ticket.write_text("01067 wird zu 1067\n", encoding="utf-8")
    print(ticket.name, ticket.stem, ticket.suffix)

    with ticket.open("a", encoding="utf-8") as f:
        f.write("Ursache: int()\n")

    text = ticket.read_text(encoding="utf-8")
    print(text.splitlines())
    print([p.name for p in folder.glob("*.md")])

print(folder.exists())  # with hat aufgeräumt
