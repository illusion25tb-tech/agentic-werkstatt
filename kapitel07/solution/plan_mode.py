"""Plan Mode: nur lesende Tools, Ergebnis ist plan.json."""
import sys
from fnmatch import fnmatch
from functools import partial
from pathlib import Path

from pydantic import ValidationError

import agent_fc
from contracts import Registry
from plan import Plan, check_plan
from repo_map import repo_map
from tools import GROUNDING, ROOT

PLAN_FILE = Path("plan.json")
KEIN_JSON = ("Kein JSON: Antworte nur mit dem Plan als "
             "JSON-Objekt, ohne Text davor.")
AUFTRAG = """Erstelle einen Plan für diese Spezifikation.
Ändere nichts, lies nur.

{spec}

Repo Map (Datei | Symbol:Startzeile):
{karte}

Antworte zum Schluss ohne Tool Call nur mit JSON:
{{"goal": "...", "steps": [{{"id": "s1", "goal": "...",
  "files": ["pfad/zur/datei.py"], "check": "pytest ...",
  "depends_on": []}}]}}
Jeder Schritt nennt vorhandene Dateien aus dem Scope und
einen check, der mit pytest oder ruff check beginnt."""


def read_only(reg: Registry) -> Registry:
    """Least Privilege: Schreibende Tools gibt es hier nicht."""
    return Registry([s for s in reg.specs.values()
                     if s.read_only])


def parse(raw: str) -> Plan:
    return Plan.model_validate_json(
        raw[raw.find("{"):raw.rfind("}") + 1])


def check(raw: str, root: Path, scope: list[str]) -> list[str]:
    try:
        plan = parse(raw)
    except ValidationError as e:
        if not raw.lstrip().startswith(("{", "```")):
            return [KEIN_JSON]
        err = e.errors()[0]
        return [f"Kein gültiger Plan: {err['msg']}, Feld "
                + str(err["loc"])]
    fehler = check_plan(plan, root)
    for s in plan.steps:
        fehler += [f"{s.id}: {f} liegt außerhalb des Scopes"
                   for f in s.files
                   if not any(fnmatch(f, m) for m in scope)]
    return fehler


def make_plan(spec: str, scope: list[str], tools=GROUNDING,
              root: Path = ROOT) -> Plan | None:
    task = AUFTRAG.format(spec=spec, karte=repo_map(root))
    out = agent_fc.run(task, read_only(tools), check=partial(
        check, root=root, scope=scope))
    if out.startswith("ABBRUCH"):
        return None
    plan = parse(out)
    PLAN_FILE.write_text(plan.model_dump_json(indent=2),
                         encoding="utf-8")      # schreibt der
    return plan                                 # Harness


if __name__ == "__main__":
    spec = Path(sys.argv[1]).read_text(encoding="utf-8")
    print(make_plan(spec, sys.argv[2:]))
