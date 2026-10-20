"""Semantisches Memory für PaketFix: Fakten mit Quelle."""
import json
import sqlite3
from pathlib import Path

from paketfix.retrieve import check_quote
from redact import redact

SCHEMA = """CREATE TABLE IF NOT EXISTS facts (
    id INTEGER PRIMARY KEY,
    fact TEXT NOT NULL,
    doc TEXT NOT NULL,
    section TEXT NOT NULL,
    quote TEXT NOT NULL,
    doc_version TEXT NOT NULL)"""


def load_versions(manifest: Path) -> dict:
    """Dateiname -> Version, aus manifest.json (Kap. 6)."""
    m = json.loads(manifest.read_text(encoding="utf-8"))
    return {d["datei"]: d["version"] for d in m["dokumente"]}


def learn(conn: sqlite3.Connection, fact: str, doc: str,
          section: str, quote: str, cs: list[dict],
          versions: dict) -> int:
    """Erst Beleg prüfen (Kap. 6), dann schwärzen, dann
    mit Dokumentversion speichern."""
    grund = check_quote(doc, section, quote, cs)
    if grund:
        raise ValueError(grund)
    conn.execute(SCHEMA)
    with conn:
        cur = conn.execute(
            "INSERT INTO facts (fact, doc, section, quote, "
            "doc_version) VALUES (?, ?, ?, ?, ?)",
            (redact(fact), doc, section, redact(quote),
             versions[doc]))
    return cur.lastrowid


def stale(conn: sqlite3.Connection, versions: dict) -> list:
    """Fakten, deren Dokument inzwischen eine andere
    Version hat. Sie gehen nicht mehr in den Kontext."""
    return [dict(r) for r in conn.execute(
        "SELECT * FROM facts") if r["doc_version"]
        != versions[r["doc"]]]
