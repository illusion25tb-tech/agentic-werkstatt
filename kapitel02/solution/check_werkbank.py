"""Prüft, ob die Werkbank aus Kapitel 2 bereit ist."""

import shutil
import subprocess
import sys


def check_python(version=sys.version_info) -> str | None:
    if tuple(version[:2]) < (3, 12):
        v = ".".join(map(str, version[:3]))
        return f"Python {v} ist zu alt, nötig ist 3.12+"
    return None


def check_program(name: str) -> str | None:
    if shutil.which(name) is None:
        return f"{name} nicht gefunden (PATH prüfen)"
    return None


def check_ignored(path: str = ".env") -> str | None:
    try:
        proc = subprocess.run(
            ["git", "check-ignore", "-q", path],
            check=False,
            capture_output=True,
        )
    except FileNotFoundError:
        return f"ohne git lässt sich {path} nicht prüfen"
    if proc.returncode == 128:
        return "kein Git-Repository (git init vergessen?)"
    if proc.returncode != 0:
        return f"{path} wird von Git NICHT ignoriert"
    return None


def main() -> int:
    errors = [
        check_python(),
        check_program("git"),
        check_program("uv"),
        check_ignored(),
    ]
    errors = [e for e in errors if e]
    for e in errors:
        print("FEHLT:", e)
    if not errors:
        print("Werkbank bereit.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
