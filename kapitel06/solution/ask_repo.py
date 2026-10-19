"""Architekturfrage an den bestellservice, mit Belegpflicht."""
import sys
from functools import partial

import agent_fc
from evidence import verify
from repo_map import repo_map
from tools import GROUNDING, ROOT

AUFTRAG = """Frage zum Repository: {frage}

Repo Map (Datei | Symbol:Startzeile):
{karte}

Erst suchen, dann lesen, dann antworten. Antworte zum
Schluss ohne Tool Call nur mit JSON in dieser Form:
{{"claims": [{{"text": "Aussage", "path": "datei.py",
  "line_start": 10, "line_end": 12,
  "quote": "wörtlich aus diesen Zeilen"}}],
 "not_found": []}}
Jede Aussage braucht Datei, Zeilen und ein Zitat, das
read_lines gezeigt hat. Gibt es etwas nicht, nenne in
not_found die Suchmuster, die keine Treffer hatten.
Widersprechen sich Doku und Code, gilt der Code."""


def ask(frage: str, budget: int = 3000) -> str:
    task = AUFTRAG.format(frage=frage,
                          karte=repo_map(ROOT, budget))
    return agent_fc.run(task, GROUNDING,
                        check=partial(verify, root=ROOT))


if __name__ == "__main__":
    print(ask(" ".join(sys.argv[1:])))
