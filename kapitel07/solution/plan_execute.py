"""Plan/Execute: Schritt für Schritt, Diff als Vorschlag."""
import os
import subprocess
from collections.abc import Callable
from pathlib import Path

from diff_budget import Budget, check_diff
from plan import Plan, Step, check_plan, order

MAX_FAILS = 2       # Fehlversuche je Schritt bis zur Neuplanung
MAX_REPLANS = 1
LOCKED = ["tests/test_acceptance_*.py"]


class PlanFailed(Exception):
    pass


def applies(diff: str, root: Path) -> list[str]:
    """git apply --check: passt der Diff? Schreibt nichts."""
    env = {**os.environ,       # nicht das umgebende Repo
           "GIT_CEILING_DIRECTORIES": str(root.parent)}
    p = subprocess.run(     # Bytes: kein \r\n unter Windows
        ["git", "apply", "--check", "-"], cwd=root, env=env,
        input=(diff + "\n").encode("utf-8"),
        capture_output=True, timeout=30, check=False)
    if p.returncode == 0:
        return []                   # Warnungen zählen nicht
    out = p.stderr.decode("utf-8", "replace").splitlines()
    fehler = [z for z in out if z.startswith("error")]
    return fehler[:3] or [f"git apply: Code {p.returncode}"]


def check_step(diff: str, step: Step, root: Path) -> list[str]:
    fehler = check_diff(diff, Budget(step.files, LOCKED))
    return fehler or applies(diff, root)


def execute(plan: Plan, propose: Callable, replan: Callable,
            root: Path) -> dict[str, str]:
    """Liefert je Schritt einen geprüften Diff-Vorschlag."""
    done, replans = {}, 0
    while True:
        offen = [s for s in order(plan) if s.id not in done]
        if not offen:
            return done
        step = offen[0]
        fehler = check_plan(plan, root)  # Annahmen gültig?
        for _ in range(0 if fehler else MAX_FAILS):
            diff = propose(step, fehler)
            fehler = check_step(diff, step, root)
            if not fehler:
                done[step.id] = diff
                break
        if step.id in done:
            continue
        if replans == MAX_REPLANS:
            raise PlanFailed(f"{step.id}: " + "; ".join(fehler))
        replans += 1
        plan = replan(plan, step, fehler)
