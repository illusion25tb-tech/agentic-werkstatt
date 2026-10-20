from datetime import date
from pathlib import Path

import yaml

from snapshots import boxes, due

HIER = Path(__file__).parent
REG = HIER / "snapshots.yaml"


def test_kasten_mit_zeile_und_daten():
    found = boxes(HIER / "fixtures" / "manuskript")
    assert found == [("99_beispiel.md", 5,
                      "Stand Oktober 2026",
                      ["03.04.2026", "15.10.2026"])]


def test_faellig_nur_was_abgelaufen_ist():
    assert due(REG, date(2026, 10, 21)) == []
    found = due(REG, date(2026, 11, 19))
    assert len(found) == 1 and "Kap. 13" in found[0]


def test_register_vollstaendig():
    keys = {"claim", "chapter", "source", "checked", "next"}
    data = yaml.safe_load(REG.read_text(encoding="utf-8"))
    for e in data["snapshots"]:
        assert set(e) == keys
        assert e["checked"] < e["next"]
