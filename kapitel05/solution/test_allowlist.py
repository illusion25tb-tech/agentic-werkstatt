from adversarial import evil_server
from allowlist import fingerprint
from mcp_bridge import connect, list_tools
from repo_server import mcp

PINS = {t.name: fingerprint(t) for t in list_tools(mcp)}


def test_ohne_allowlist_landet_alles_im_kontext():
    with connect(mcp, evil_server.mcp) as bridge:
        texte = [s["function"]["description"]
                 for s in bridge.schemas()]
    assert len(texte) == 4
    assert any("../.env" in t for t in texte)


def test_unbekanntes_tool_wird_gefiltert():
    meldungen = []
    with connect(mcp, evil_server.mcp, pins=PINS,
                 log=meldungen.append) as bridge:
        assert set(bridge.tools) == {"list_files", "read_file",
                                     "search"}
    assert meldungen == ["Tool 'format_hint' abgelehnt: neu"]


def test_geaenderte_beschreibung_wird_gefiltert():
    meldungen = []
    with connect(evil_server.rug_pull(), pins=PINS,
                 log=meldungen.append) as bridge:
        assert set(bridge.tools) == {"list_files", "read_file"}
    assert meldungen == ["Tool 'search' abgelehnt: geändert"]


def test_gleichnamiges_tool_ueberschreibt_nicht():
    meldungen = []
    with connect(mcp, evil_server.rug_pull(),
                 log=meldungen.append) as bridge:
        _, search = bridge.tools["search"]
    assert "../.env" not in search.description
    assert "Tool 'search' doppelt, verworfen" in meldungen


def test_fingerabdruck_stabil():
    a, b = list_tools(mcp), list_tools(mcp)
    assert [fingerprint(t) for t in a] == [
        fingerprint(t) for t in b]
