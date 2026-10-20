"""Episodisches Projekt-Memory in SQLite, nur Stdlib."""
import json
import re
import sqlite3
from datetime import date, timedelta

SCHEMA = """CREATE TABLE IF NOT EXISTS episodes (
    id INTEGER PRIMARY KEY,
    task TEXT NOT NULL,         -- Auftrag des Runs
    files TEXT NOT NULL,        -- JSON-Liste berührter Dateien
    outcome TEXT NOT NULL,      -- Ausgang
    lesson TEXT NOT NULL,       -- was sich merken lohnt
    source TEXT NOT NULL,       -- welcher Run, welche Prüfung
    verified INTEGER NOT NULL,  -- 1 = vom Harness geprüft
    valid_until TEXT NOT NULL,  -- ISO-Datum
    created TEXT NOT NULL)"""
WORT = re.compile(r"\w{4,}(?:\.\w+)?")    # auch labels.py


def open_db(path: str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    return conn


def record(conn: sqlite3.Connection, task: str, files: list,
           outcome: str, lesson: str, source: str,
           verified: bool = False, days: int = 90,
           today: date | None = None) -> int:
    today = today or date.today()
    until = (today + timedelta(days=days)).isoformat()
    with conn:                  # committet, schließt nicht
        cur = conn.execute(
            "INSERT INTO episodes (task, files, outcome, "
            "lesson, source, verified, valid_until, created) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (task, json.dumps(files), outcome, lesson, source,
             int(verified), until, today.isoformat()))
    return cur.lastrowid


def recall(conn: sqlite3.Connection, task: str, files=(),
           k: int = 3, today: date | None = None) -> list:
    """Top-k nach Wort- und Dateiüberlappung, nur gültige."""
    heute = (today or date.today()).isoformat()
    worte = set(WORT.findall(task.lower()))
    scored = []
    for row in conn.execute("SELECT * FROM episodes WHERE "
                            "valid_until >= ?", (heute,)):
        ep = dict(row, files=json.loads(row["files"]))
        text = f"{ep['task']} {ep['lesson']}".lower()
        score = (len(worte & set(WORT.findall(text)))
                 + 2 * len(set(files) & set(ep["files"])))
        if score:
            scored.append((score, ep["id"], ep))
    scored.sort(key=lambda t: (-t[0], -t[1]))  # neuere vorn
    return [ep for _, _, ep in scored[:k]]
