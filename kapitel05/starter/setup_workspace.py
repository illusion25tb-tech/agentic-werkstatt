"""Macht workspace/ zu einem Git-Repository mit zwei Commits."""
import json
import subprocess
from pathlib import Path

W = Path("workspace")
DATEI = W / "bestellungen" / "4711.json"


def git(*args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=Nordlicht Shop",
         "-c", "user.email=shop@nordlicht.example", *args],
        cwd=W, check=True, capture_output=True)


def schreibe(menge_bitsatz: int) -> None:
    positionen = [
        {"artikel": "Akkuschrauber", "menge": 2,
         "preis": 89.90},
        {"artikel": "Bitsatz", "menge": menge_bitsatz,
         "preis": 12.50},
    ]
    daten = {"nr": 4711, "positionen": positionen}
    DATEI.parent.mkdir(parents=True, exist_ok=True)
    DATEI.write_text(json.dumps(daten, indent=1) + "\n",
                     encoding="utf-8")


if __name__ == "__main__":
    if (W / ".git").exists():
        raise SystemExit("workspace/ ist schon ein Repository")
    W.mkdir(exist_ok=True)
    git("init", "-q")
    schreibe(2)
    git("add", ".")
    git("commit", "-q", "-m", "Bestellung 4711 angelegt")
    schreibe(3)
    git("commit", "-q", "-am",
        "Bestellung 4711: Bitsatz nachbestellt")
    print("workspace/ ist jetzt ein Git-Repository")
