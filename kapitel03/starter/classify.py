"""Klassifiziert Issues. Build: nur eine Bitte um JSON."""
import sys
from pathlib import Path

from llm import ask_model

SYSTEM = """Ordne das Ticket eines Online-Shops ein.
Antworte als JSON mit den Feldern kategorie (bug, feature,
frage oder sicherheit), prioritaet (niedrig, mittel oder
hoch) und begruendung (ein Satz)."""

for pfad in map(Path, sys.argv[1:]):
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user",
                 "content": pfad.read_text(encoding="utf-8")}]
    antwort = ask_model(messages)
    print(pfad.stem, " ".join(antwort.split()), flush=True)
