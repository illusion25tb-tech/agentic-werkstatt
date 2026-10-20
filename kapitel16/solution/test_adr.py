import re
from pathlib import Path

HIER = Path(__file__).parent
CODE = HIER.parent.parent          # Wurzel des Repositorys
ADRS = sorted((HIER / "docs" / "adr").glob("*.md"))


def test_belege_existieren():
    for adr in ADRS:
        text = adr.read_text(encoding="utf-8")
        beleg = text.split("## Beleg", 1)[1].split("##")[0]
        pfade = re.findall(r"kapitel\d+/[\w./-]+", beleg)
        assert pfade, f"{adr.name}: kein Beleg"
        for p in pfade:
            assert (CODE / p).exists(), f"{adr.name}: {p}"


def test_zeilen_passen_in_den_satz():
    for adr in ADRS:
        for z in adr.read_text(encoding="utf-8").splitlines():
            assert len(z) <= 64, z
