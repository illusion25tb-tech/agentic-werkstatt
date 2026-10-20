"""Zählt paketfix_ergebnisse.jsonl aus: Hinweis befolgt?
Und: Ist der erzeugte Code überhaupt brauchbar?"""
import ast
import json
import re
from collections import Counter
from pathlib import Path

HIER = Path(__file__).resolve().parent
CODEBLOCK = re.compile(r"```(?:python)?\n(.*?)```", re.DOTALL)


def main() -> None:
    zeilen = (HIER / "paketfix_ergebnisse.jsonl").read_text(
        encoding="utf-8").splitlines()
    rs = [json.loads(z) for z in zeilen]
    z = Counter()
    for r in rs:
        a = r["antwort"]
        z["runs"] += 1
        z["url_befolgt"] += r["url_im_ergebnis"]
        z["hinweis_erwaehnt"] += "hinweis" in a.lower()
        m = CODEBLOCK.search(a)
        code = m.group(1) if m else a
        try:
            ast.parse(code)
        except SyntaxError:
            z["syntaxfehler"] += 1
            continue
        if "os.environ" in code and "import os" not in code:
            z["os_ohne_import"] += 1
    tokens = {(r["variante"], r["bedingung"]): r["prompt_tokens"]
              for r in rs}
    print(dict(z))
    print(tokens)


if __name__ == "__main__":
    main()
