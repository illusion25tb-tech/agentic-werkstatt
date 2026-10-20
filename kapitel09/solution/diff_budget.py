"""Unified Diff zählen und gegen Budget und Scope prüfen."""
from dataclasses import dataclass
from fnmatch import fnmatch


def _name(header: str) -> str:
    name = header[4:].split("\t")[0].strip()
    return name.removeprefix("a/").removeprefix("b/")


def numstat(diff: str) -> dict[str, list[int]]:
    """Wie git diff --numstat: Pfad -> [hinzu, entfernt].

    Zählt jede +/- Zeile, auch wenn die Hunk-Köpfe nicht
    stimmen. Ob der Diff sauber passt, prüft git apply.
    """
    stat, path = {}, None
    zeilen = diff.splitlines()
    for i, line in enumerate(zeilen):
        nxt = zeilen[i + 1] if i + 1 < len(zeilen) else ""
        if line.startswith("--- ") and nxt.startswith("+++ "):
            neu, alt = _name(nxt), _name(line)
            path = alt if neu == "/dev/null" else neu
            stat.setdefault(path, [0, 0])
        elif line.startswith("+++ ") and i and zeilen[
                i - 1].startswith("--- "):
            continue                    # zweite Kopfzeile
        elif path and line[:1] in ("+", "-"):
            stat[path][line[0] == "-"] += 1
    return stat


@dataclass
class Budget:
    allowed: list[str]          # Muster, z. B. bestellservice/*
    locked: list[str]           # nie anfassen
    max_files: int = 5          # Beispielwerte
    max_lines: int = 150


def check_diff(diff: str, b: Budget) -> list[str]:
    """Einwände; leer heißt: Vorschlag liegt im Rahmen."""
    stat = numstat(diff)
    if not stat:
        return ["Kein Unified Diff (--- a/, +++ b/, @@)"]
    fehler = []
    for p in stat:
        if any(fnmatch(p, m) for m in b.locked):
            fehler.append(f"{p} ist gesperrt (Acceptance Test)")
        elif not any(fnmatch(p, m) for m in b.allowed):
            fehler.append(f"{p} liegt außerhalb des Scopes")
    if len(stat) > b.max_files:
        fehler.append(f"{len(stat)} Dateien, erlaubt sind "
                      f"{b.max_files}")
    lines = sum(a + r for a, r in stat.values())
    if lines == 0:                      # nur Kontext, kein +/-
        fehler.append("Der Diff ändert keine Zeile.")
    if lines > b.max_lines:
        fehler.append(f"{lines} geänderte Zeilen, erlaubt sind "
                      f"{b.max_lines}. Kleiner schneiden.")
    return fehler
