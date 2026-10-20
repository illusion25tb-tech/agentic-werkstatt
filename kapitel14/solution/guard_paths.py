"""git diff --name-status BASIS...HEAD | python guard_paths.py

Pflicht-Job für PRs von Agenten: Exit 1, wenn der Diff
eine Prüfung berührt. Neue Testdateien sind erlaubt,
geänderte, gelöschte oder umbenannte nicht."""
import sys
from fnmatch import fnmatchcase

GESCHUETZT = ("*.github/*", "*CODEOWNERS", "*evals/*",
              "*conftest.py", "*pyproject.toml")
TESTS = ("*tests/*", "*test_*.py")


def hits(path: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatchcase(path, p) for p in patterns)


def violations(lines: list[str]) -> list[str]:
    """lines: Ausgabe von git diff --name-status."""
    out = []
    for line in filter(str.strip, lines):
        status, *paths = line.split("\t")   # R100 alt neu
        for p in paths:
            if hits(p, GESCHUETZT):
                out.append(f"{status[0]} {p}: geschützt")
            elif hits(p, TESTS) and status != "A":
                out.append(f"{status[0]} {p}: bestehender Test")
    return out


def main() -> int:
    found = violations(sys.stdin.read().splitlines())
    for f in found:
        print("ROT:", f)
    print(f"guard_paths: {len(found)} Verstoß/Verstöße")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
