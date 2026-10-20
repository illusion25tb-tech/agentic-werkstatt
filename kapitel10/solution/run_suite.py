"""python run_suite.py --runs 3 [--only NL-111,NL-118]

Alle Aufgaben × Runs, jede Zeile sofort in results.jsonl.
Ein zweiter Aufruf setzt fort, statt von vorn zu beginnen."""
import argparse
import json
import os
import tempfile
from pathlib import Path

from metrics import load_prices
from run_one import BUTLER, HIER, run_one
from tasks import load_tasks

CODE = HIER.parents[1]                  # Begleit-Repository


def done(results: Path) -> set[tuple[str, int]]:
    if not results.is_file():
        return set()
    lines = results.read_text(encoding="utf-8").splitlines()
    return {(r["task"], r["run"]) for r in map(json.loads,
                                               lines)}


def suite(tasks, runs: int, results: Path, **kw) -> int:
    fertig, neu = done(results), 0
    for i in range(1, runs + 1):        # erst Run 1 für alle
        for t in tasks:
            if (t.id, i) in fertig:
                continue
            rec = run_one(t, i, **kw)
            with results.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False)
                        + "\n")
            print(t.id, i, rec["outcome"], flush=True)
            neu += 1
    return neu


def main(argv=None) -> None:
    import cli  # Kapitel 9
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--only", default="")
    ap.add_argument("--out", type=Path,
                    default=HIER / "ergebnisse")
    ap.add_argument("--python", default=str(
        CODE / "bestellservice/.venv/Scripts/python.exe"))
    a = ap.parse_args(argv)
    tasks = load_tasks(CODE / "evals/tasks.json", CODE)
    if a.only:
        tasks = [t for t in tasks if t.id in a.only.split(",")]
    a.out.mkdir(parents=True, exist_ok=True)
    md = BUTLER / "fixtures/AGENTS_bestellservice.md"
    with tempfile.TemporaryDirectory(
            ignore_cleanup_errors=True) as work:
        neu = suite(
            tasks, a.runs, a.out / "results.jsonl",
            source=CODE / "bestellservice", work=Path(work),
            out=a.out, model=cli.model_from_env(),
            model_name=os.environ["LLM_MODEL"],
            python=a.python, prices=load_prices(
                HIER / "prices.toml"),
            agents_md=md)
    print(f"{neu} neue Runs in {a.out / 'results.jsonl'}")


if __name__ == "__main__":
    main()
