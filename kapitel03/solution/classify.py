"""Klassifiziert Issues, eine JSON-Zeile pro Issue."""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from pydantic import ValidationError

from llm import LAST_USAGE, ask_model
from schema import IssueKlasse

TOKENS = Counter()  # Summe über alle Aufrufe dieses Programms

SYSTEM = """Du ordnest Tickets eines Online-Shops ein.
Antworte nur mit einem JSON-Objekt mit genau diesen Feldern:
"kategorie": "bug", "feature", "frage" oder "sicherheit"
"prioritaet": "niedrig", "mittel" oder "hoch"
"begruendung": ein Satz, höchstens 300 Zeichen
"dateien": im Ticket genannte Dateien, sonst []
Erfinde keine Dateinamen."""


def classify(text: str, retries: int = 1) -> IssueKlasse:
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": text}]
    for _ in range(retries + 1):
        raw = ask_model(messages)
        for feld in ("prompt_tokens", "completion_tokens"):
            TOKENS[feld] += LAST_USAGE.get(feld, 0)
        try:
            return IssueKlasse.model_validate_json(raw)
        except ValidationError as e:
            err = e.errors()[0]
            feld = ".".join(map(str, err["loc"])) or "Objekt"
            messages += [
                {"role": "assistant", "content": raw},
                {"role": "user", "content":
                    f"FEHLER in der Antwort, Feld {feld!r}: "
                    f"{err['msg']}. Antworte nur mit dem "
                    "korrigierten JSON-Objekt."}]
    raise ValueError(f"ungültig nach Retry: {raw[:80]}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("dateien", nargs="+", type=Path)
    args = p.parse_args(argv)
    code = 0
    for pfad in args.dateien:
        try:
            k = classify(pfad.read_text(encoding="utf-8"))
            out = {"issue": pfad.stem, **k.model_dump()}
        except ValueError as e:
            out = {"issue": pfad.stem, "fehler": str(e)}
            code = 1
        print(json.dumps(out, ensure_ascii=False), flush=True)
    print(f"Tokens: {dict(TOKENS)}", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
