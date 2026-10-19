"""Prüfsignal für NL-101: Regressionstest gegen vier Code-Stände.

Basis, nur >=, nur Decimal, beides (= solutions/NL-101.patch).
Aufruf mit dem Python der bestellservice-venv (pytest, fastapi, httpx).
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CODE = Path(__file__).resolve().parents[2]
PATCH = CODE / "solutions" / "NL-101.patch"


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True,
                   capture_output=True)


def run(variant: str, tmp: Path) -> str:
    ws = tmp / variant
    shutil.copytree(CODE / "bestellservice", ws, ignore=shutil.
                    ignore_patterns(".venv", "__pycache__", ".*cache"))
    git(ws, "init", "-q")
    git(ws, "apply", "--include=tests/*", str(PATCH))
    if variant in ("nur_decimal", "beides"):
        git(ws, "apply", "--include=bestellservice/cart.py", str(PATCH))
    if variant in ("nur_ge", "beides"):
        f = ws / "bestellservice" / "shipping_costs.py"
        f.write_text(f.read_text(encoding="utf-8").replace(
            "subtotal > FREE", "subtotal >= FREE"), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider",
         "-rf", "tests/test_nl101.py"],
        cwd=ws, capture_output=True, text=True)
    summary = [ln for ln in proc.stdout.splitlines()
               if ln.startswith("FAILED") or " passed" in ln
               or " failed" in ln]
    return "\n".join(summary)


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        for v in ("basis", "nur_ge", "nur_decimal", "beides"):
            print(f"== {v}\n{run(v, Path(tmp))}")
