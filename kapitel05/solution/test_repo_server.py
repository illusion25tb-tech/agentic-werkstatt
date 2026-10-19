import pytest
from mcp import Client

from repo_server import mcp


@pytest.mark.anyio
async def test_genau_drei_tools_read_only():
    async with Client(mcp) as client:
        tools = (await client.list_tools()).tools
    assert {t.name for t in tools} == {
        "list_files", "read_file", "search"}
    for t in tools:
        assert t.annotations.read_only_hint is True
        assert t.annotations.destructive_hint is False


@pytest.mark.anyio
async def test_lesen_und_suchen():
    async with Client(mcp) as client:
        r = await client.call_tool("list_files",
                                   {"path": "bestellservice"})
        assert "bestellservice/tariffs.py" in r.content[0].text
        r = await client.call_tool(
            "search", {"text": "FREE_SHIPPING_FROM"})
        assert "bestellservice/shipping_costs.py" in (
            r.content[0].text)
        r = await client.call_tool("read_file",
                                   {"path": "README.md"})
        assert r.structured_content["result"].startswith(
            "# bestellservice")


@pytest.mark.anyio
async def test_pfad_ausserhalb_ist_fehlerergebnis():
    async with Client(mcp) as client:
        for p in ["../.env", "../kapitel05/solution/tools.py"]:
            r = await client.call_tool("read_file", {"path": p})
            assert r.is_error is True
            assert "außerhalb" in r.content[0].text, p


@pytest.mark.anyio
async def test_fehlende_datei_mit_hinweis():
    async with Client(mcp) as client:
        r = await client.call_tool("read_file",
                                   {"path": "porto.py"})
    assert r.is_error and "list_files" in r.content[0].text
