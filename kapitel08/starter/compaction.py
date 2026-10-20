"""Context Compaction: Kopf und Ende bleiben, Mitte kurz."""
import re

from context_builder import est, msg_text
from llm import _post

MARK = "[Zusammenfassung früherer Schritte, vom Harness]"
PFAD = re.compile(r"[\w./-]+\.(?:py|md|json|toml)\b")
PROMPT = """Fasse die folgenden Schritte eines Coding Agents
für seine Fortsetzung zusammen. Höchstens zehn Sätze.
Behalte: was gesucht und gefunden wurde, mit Datei und
Zeile; Hypothesen, die verworfen wurden, und warum;
den nächsten geplanten Schritt. Lass weg: Begrüßungen,
Wiederholungen, vollständige Dateiinhalte.
Erfinde nichts, was nicht in den Schritten steht.

Schritte:
"""


def size(messages: list[dict]) -> int:
    return sum(est(msg_text(m)) for m in messages)


def compact(messages: list[dict], max_tokens: int,
            summarize, keep_last: int = 3) -> list[dict]:
    if size(messages) <= max_tokens:
        return messages
    head = next(i for i, m in enumerate(messages)
                if m["role"] == "user") + 1    # bis Auftrag
    starts = [i for i, m in enumerate(messages)
              if i >= head and m["role"] == "assistant"]
    if len(starts) <= keep_last:
        return messages     # nichts Altes zum Verdichten
    cut = starts[-keep_last]    # Schrittgrenze: Paare bleiben
    middle = messages[head:cut]
    text = "\n".join(f"{m['role']}: {msg_text(m)}"
                     for m in middle)
    pfade = sorted(set(PFAD.findall(text)))
    fehler = [m["content"][:200] for m in middle
              if m["role"] == "tool"
              and m["content"].startswith("FEHLER")]
    summary = "\n".join([
        MARK, summarize(PROMPT + text),
        "Pfade aus diesen Schritten: " + ", ".join(pfade),
        "Fehlermeldungen wörtlich:", *fehler])
    neu = (messages[:head]
           + [{"role": "user", "content": summary}]
           + messages[cut:])
    return neu if size(neu) < size(messages) else messages


def model_summary(prompt: str) -> str:
    """Ein zusätzlicher Modellaufruf, ohne Tools."""
    data = _post({"messages": [{"role": "user",
                                "content": prompt}]})
    return data["choices"][0]["message"]["content"]
