"""python cli.py ISSUE.md --repo ARBEITSKOPIE

Branch, Plan, Freigabe, Umsetzung, Diff, Commit. Push und
Pull Request bleiben beim Menschen."""
import argparse
import hashlib
import json
import os
from pathlib import Path

from pydantic_ai.exceptions import (
    UnexpectedModelBehavior,
    UsageLimitExceeded,
)

import agent
import git_ops
from deps import Deps
from diff_budget import Budget
from memory import open_db
from policy import MODES, Policy
from tools_exec import HandOver
from write_policy import remember

ACCEPT = "tests/test_acceptance_*.py"   # nie anfassen
BUDGET = Budget(["bestellservice/*.py", "tests/test_*.py"],
                [ACCEPT], max_files=3, max_lines=60)


def ask(risk: str, tool: str, args: dict) -> bool:
    print(f"\n[{risk}] {tool} "
          + json.dumps(args, ensure_ascii=False)[:600])
    return input("Freigeben? [j/N] ").strip().lower() == "j"


def fingerprint(repo: Path) -> dict[str, str]:
    """Prüfsummen der Acceptance Tests vor dem Run."""
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(repo.glob(ACCEPT))}


def model_from_env():
    from pydantic_ai.models.ollama import OllamaModel
    from pydantic_ai.providers.ollama import OllamaProvider
    settings = {"max_tokens": 2000}     # Antwort-Obergrenze
    temp = os.environ.get("LLM_TEMPERATURE")  # wie llm.py
    if temp:
        settings["temperature"] = float(temp)
    return OllamaModel(
        os.environ["LLM_MODEL"], settings=settings,
        provider=OllamaProvider(
            base_url=os.environ["LLM_BASE_URL"]))


def main(argv=None, approve=ask, model=None) -> int:
    os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
    ap = argparse.ArgumentParser(prog="butler")
    ap.add_argument("issue", type=Path)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--mode", choices=MODES,
                    default="interaktiv")
    ap.add_argument("--python", default="python")
    ap.add_argument("--out", type=Path, default=Path("."))
    a = ap.parse_args(argv)
    repo, ticket = a.repo.resolve(), a.issue.read_text("utf-8")
    model = model or model_from_env()
    issue = a.issue.stem                        # NL-107
    base = git_ops.start(repo, issue)           # Netz 1
    locked = fingerprint(repo)
    tests = {p.relative_to(repo).as_posix()
             for p in repo.glob("tests/test_*.py")}
    deps = Deps(repo, Policy(a.mode, tests), approve, BUDGET,
                a.out / f"trace_{issue}.jsonl", a.python)
    try:
        plan = agent.make_plan(ticket, deps, model)
        nein = deps.policy.check("plan", plan.model_dump(),
                                 approve)
        if nein:                        # Gate 1: der Plan
            git_ops.discard(repo, base, issue)
            print(f"Keine Umsetzung ({nein}). Branch weg.")
            return 1
        report = agent.execute(ticket, plan, deps, model)
    except (HandOver, UsageLimitExceeded,
            UnexpectedModelBehavior) as e:
        agent.log(deps, abort=f"{type(e).__name__}: {e}")
        print(f"Übergabe an Menschen: {e}. Branch butler/"
              f"{issue} bleibt zum Ansehen stehen.")
        return 2
    if fingerprint(repo) != locked:             # Netz 2
        print("Acceptance Test verändert. Kein Commit.")
        return 3
    print(git_ops.git(repo, "diff", "HEAD", "--stat"))
    if deps.policy.check("commit", {"issue": issue},
                         approve):      # Gate 2: der Commit
        print("Kein Commit. Diff liegt im Branch.")
        return 4
    sha = git_ops.commit(repo, f"{issue}: {report.summary}")
    write_outputs(a.out, issue, report, deps, sha)
    return 0


def write_outputs(out: Path, issue: str, report, deps: Deps,
                  sha: str) -> None:
    """PR-Text für den Menschen, Episode fürs Memory."""
    (out / f"report_{issue}.json").write_text(
        report.model_dump_json(indent=1), encoding="utf-8")
    belege = [f"- `{c.path}:{c.line_start}-{c.line_end}` "
              f"{c.text}" for c in report.reasons]
    pr = [f"## {issue}: {report.summary}", "", *belege, "",
          f"Tests: {report.tests}", "Risiken: "
          + "; ".join(report.risks or ["keine genannt"]),
          f"Freigaben: {deps.policy.asked}, Commit {sha}"]
    (out / f"pr_{issue}.md").write_text(
        "\n".join(pr) + "\n", encoding="utf-8")
    try:                                # Kapitel 8
        remember(open_db(str(out / "memory.db")), {
            "task": issue, "files": report.changed_files,
            "outcome": "Suite grün, committet",
            "lesson": report.summary, "verified": True,
            "source": f"butler {issue}, Commit {sha}",
            "days": 90}, deps.repo)
    except ValueError as e:
        print(f"Keine Episode gespeichert: {e}")


if __name__ == "__main__":
    raise SystemExit(main())
