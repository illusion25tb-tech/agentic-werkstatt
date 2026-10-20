"""Abschnitte der PaketFix-Dokumente finden, nur Stdlib."""
import math
import re
from collections import Counter
from pathlib import Path

WORT = re.compile(r"\w{3,}")


def chunks(korpus: Path) -> list[dict]:
    """Zerlegt jede .md-Datei an ihren Überschriften."""
    out = []
    for f in sorted(korpus.glob("*.md")):
        titel, zeilen = "(Anfang)", []
        for z in f.read_text(encoding="utf-8").splitlines():
            if z.startswith("#"):
                out.append(_chunk(f.name, titel, zeilen))
                titel, zeilen = z.lstrip("# "), []
            zeilen.append(z)
        out.append(_chunk(f.name, titel, zeilen))
    return [c for c in out if c["text"].strip()]


def _chunk(datei: str, titel: str, zeilen: list) -> dict:
    text = "\n".join(zeilen)
    w = Counter(WORT.findall(text.lower()))
    for t in WORT.findall(titel.lower()):
        w[t] += 2               # Überschrift zählt dreifach
    return {"doc": datei, "section": titel, "text": text,
            "woerter": w}


def retrieve(frage: str, cs: list[dict], k: int = 3,
             k1: float = 1.2, b: float = 0.75) -> list[dict]:
    """BM25 nach Robertson/Zaragoza, ohne Vektoren."""
    n = len(cs)
    avg = sum(c["woerter"].total() for c in cs) / n
    scores = []
    for c in cs:
        s, laenge = 0.0, c["woerter"].total()
        for w in set(WORT.findall(frage.lower())):
            df = sum(1 for x in cs if w in x["woerter"])
            tf = c["woerter"][w]
            idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
            s += idf * tf * (k1 + 1) / (
                tf + k1 * (1 - b + b * laenge / avg))
        scores.append((s, c))
    scores.sort(key=lambda t: -t[0])
    return [dict(c, score=round(s, 2))
            for s, c in scores[:k] if s > 0]


def check_quote(doc: str, section: str, quote: str,
                cs: list[dict]) -> str | None:
    """Belegpflicht für Prosa: Dokument, Abschnitt, Zitat."""
    for c in cs:
        if (c["doc"], c["section"]) == (doc, section):
            if " ".join(quote.split()) in " ".join(
                    c["text"].split()):
                return None
            return f"Zitat steht nicht in {doc} § {section}"
    return f"Abschnitt {section!r} gibt es in {doc} nicht"
