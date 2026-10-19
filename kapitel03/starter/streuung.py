"""Stellt dieselbe Frage n-mal und zählt die Antworten."""
import sys
from collections import Counter
from pathlib import Path

from llm import ask_model

FRAGE = "Welche Priorität hat dieses Ticket?\n\n"


def streuung(ticket: str, n: int = 5) -> Counter:
    messages = [{"role": "user", "content": FRAGE + ticket}]
    antworten = Counter()
    for _ in range(n):
        antwort = ask_model(messages)
        antworten[" ".join(antwort.split())[:60]] += 1
    return antworten


if __name__ == "__main__":
    ticket = Path(sys.argv[1]).read_text(encoding="utf-8")
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    for antwort, anzahl in streuung(ticket, n).most_common():
        print(f"{anzahl}x  {antwort}")
