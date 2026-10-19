import shutil
from pathlib import Path

import pytest

import search_rg
from contracts import ToolError
from tools import GROUNDING, ROOT

FIXTURE = Path(__file__).parent / "fixtures" / "rg_weight.jsonl"


@pytest.fixture
def ohne_rg(monkeypatch):
    """Erzwingt den Fallback in reinem Python."""
    monkeypatch.setattr(search_rg.shutil, "which",
                        lambda name: None)


def test_treffer_mit_zeile(ohne_rg):
    out = GROUNDING.call("search", {"pattern": "def .*weight",
                                    "path": "bestellservice"})
    assert "/orders.py:145: def order_weight(" in out
    assert "/labels.py:45: def _parcel_weight(" in out


def test_rg_json_gleiche_form():
    hits = search_rg.parse_rg(FIXTURE.read_text("utf-8"))
    assert ("bestellservice/orders.py", 145) in [
        (p, n) for p, n, _ in hits]
    assert len(hits) == 8     # begin, end, summary übergangen


def test_fallback_und_rg_liefern_dasselbe(ohne_rg):
    py = search_rg._py("def .*weight", ROOT, ROOT)
    rg = search_rg.parse_rg(FIXTURE.read_text("utf-8"))
    assert sorted(py) == sorted(rg)


@pytest.mark.skipif(shutil.which("rg") is None,
                    reason="ripgrep nicht installiert")
def test_echtes_rg():
    out = search_rg.search("FREE_SHIPPING_FROM", ".", ROOT)
    assert "bestellservice/shipping_costs.py:15:" in out


def test_keine_treffer_und_kaputte_regex(ohne_rg):
    out = GROUNDING.call("search", {"pattern": "teilstorno"})
    assert out.startswith("Keine Treffer")
    with pytest.raises(ToolError) as e:
        GROUNDING.call("search", {"pattern": "def ("})
    assert e.value.kind == "invalid_args"


def test_trefferzahl_begrenzt(ohne_rg):
    out = GROUNDING.call("search", {"pattern": "def "})
    assert len(out.splitlines()) == search_rg.MAX_HITS + 1
    assert "gekürzt" in out.splitlines()[-1]


def test_pfadgrenze(ohne_rg):
    for p in ["..", "../kapitel06"]:
        with pytest.raises(ToolError) as e:
            GROUNDING.call("search",
                           {"pattern": "def", "path": p})
        assert e.value.kind in ("permission", "invalid_args")


def test_read_lines_mit_nummern():
    out = GROUNDING.call("read_lines", {
        "path": "bestellservice/orders.py",
        "start": 145, "end": 146})
    assert out.splitlines()[0] == (
        " 145| def order_weight(items: list[dict]) -> float:")


def test_read_lines_bereich_ausserhalb():
    for start, end in [(500, 510), (0, 3), (20, 10)]:
        with pytest.raises(ToolError) as e:
            GROUNDING.call("read_lines", {
                "path": "bestellservice/tracking.py",
                "start": start, "end": end})
        assert e.value.kind == "invalid_args"


def test_read_lines_kappt_auf_maximum():
    out = GROUNDING.call("read_lines", {
        "path": "bestellservice/orders.py",
        "start": 1, "end": 400})
    assert len(out.splitlines()) == 60
