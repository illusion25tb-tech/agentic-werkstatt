"""Nachgestellter Einstiegs-Trace: geskriptetes Modell, kein
echter Modelllauf. read_file liefert für die Versandregeln
einen leeren String, der Guard ist aus.

python einstieg.py  -> einstieg/trace.jsonl, spans.jsonl"""
import json
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent / "solution"))

from opentelemetry.sdk.trace.export import ConsoleSpanExporter

import agent
import tools
from otel_spans import setup

OUT = HIER / "einstieg"
WS = OUT / "workspace"
(WS / "bestellungen").mkdir(parents=True, exist_ok=True)
(WS / "konfig").mkdir(exist_ok=True)
ORIGINAL = (HIER.parent / "solution" / "workspace"
            / "bestellungen" / "4711.json")
(WS / "bestellungen" / "4711.json").write_text(
    ORIGINAL.read_text(encoding="utf-8"), encoding="utf-8")
(WS / "konfig" / "versand.toml").write_text(
    "versandkosten = 4.90\nfrei_ab = 50.00\n", encoding="utf-8")
tools.WORKDIR = WS.resolve()


def lies(path: str) -> str:
    if path.startswith("konfig/"):
        return ""                       # die Störung
    return tools.read_file(path)


def j(thought, tool, **args):
    return json.dumps({"thought": thought, "tool": tool,
                       "args": args}, ensure_ascii=False)


SKRIPT = iter([
    j("Ich sehe mich um.", "list_files", path="."),
    j("Ich lese die Bestellung.", "read_file",
      path="bestellungen/4711.json"),
    j("Warenwert ausrechnen.", "calculator",
      expression="2*89.90 + 3*12.50"),
    j("Wo stehen die Versandregeln?", "list_files",
      path="konfig"),
    j("Ich lese die Versandregeln.", "read_file",
      path="konfig/versand.toml"),
    j("Die Datei enthält keine Versandregeln. Ich nehme den "
      "üblichen Standardversand von 4,90 EUR an.",
      "calculator", expression="217.3 + 4.90"),
    j("Fertig.", "finish",
      answer="Bestellung 4711 kostet 222,20 EUR "
             "inkl. Versand."),
])

if __name__ == "__main__":
    agent.TRACE = OUT / "trace.jsonl"
    agent.TRACE.unlink(missing_ok=True)
    agent.TOOLS["read_file"] = lies
    agent.guard = str                   # Guard aus
    agent.ask_model = lambda messages: next(SKRIPT)
    with (OUT / "spans.jsonl").open("w", encoding="utf-8") as f:
        setup(ConsoleSpanExporter(
            out=f, formatter=lambda s: s.to_json(indent=None)
            + "\n"))
        print(agent.run("Was zahlt der Kunde für Bestellung "
                        "4711 einschließlich Versand?"))
