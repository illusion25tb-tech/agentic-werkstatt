"""Weg 3 aus Kapitel 1: der Agent aus Kapitel 4 bekommt NL-101.

Unverändert: agent.py und tools.py aus kapitel04/solution
(lesen, list_files, git, calculator; kein Schreiben, keine Tests).
Workspace: Kopie des bestellservice plus Ticket, als Git-Repository,
in einem Ordner außerhalb des Begleit-Repositorys (Argument 1).
Traces: agent_traces/<modell>_<run>.jsonl, Antworten: agent_runs.jsonl
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE = HERE.parents[1]
TASK = ("Bearbeite das Ticket in NL-101.md. Finde die Ursache im "
        "Code und nenne Datei, Stelle und Korrektur.")


def make_workspace(base: Path) -> None:
    ws = base / "workspace"
    if ws.exists():
        return
    ignore = shutil.ignore_patterns(".venv", "__pycache__", ".*cache")
    shutil.copytree(CODE / "bestellservice", ws, ignore=ignore)
    shutil.copy(CODE / "issues" / "NL-101.md", ws)
    for args in (["init", "-q"], ["add", "."],
                 ["commit", "-q", "-m", "Basisstand"]):
        subprocess.run(["git", "-c", "user.name=x",
                        "-c", "user.email=x@x", *args],
                       cwd=ws, check=True)


if __name__ == "__main__":
    base = Path(sys.argv[1]).resolve()
    models = sys.argv[2:] or ["gemma3:4b", "llama3.2:3b", "phi4-mini"]
    make_workspace(base)
    os.chdir(base)                       # tools.py: WORKDIR relativ
    sys.path[:0] = [str(HERE), str(CODE / "kapitel04" / "solution")]
    os.environ.setdefault("LLM_TEMPERATURE", "0.7")
    import agent                         # noqa: E402
    traces = HERE / "agent_traces"
    traces.mkdir(exist_ok=True)
    for model in models:
        os.environ["LLM_MODEL"] = model
        for run in range(1, 4):
            name = model.replace(":", "-") + f"_{run}.jsonl"
            agent.TRACE = traces / name
            agent.TRACE.unlink(missing_ok=True)
            answer = agent.run(TASK)
            rec = {"model": model, "run": run, "answer": answer}
            with (HERE / "agent_runs.jsonl").open(
                    "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(model, run, answer[:120].replace("\n", " "))
