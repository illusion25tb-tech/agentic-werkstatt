import pytest
from mcp import Client

from repo_server import mcp


@pytest.mark.anyio
async def test_drei_tools_read_only():
    async with Client(mcp) as client:
        tools = (await client.list_tools()).tools
    assert {t.name for t in tools} == {
        "search", "read_lines", "outline"}
    assert all(t.annotations.read_only_hint for t in tools)


@pytest.mark.anyio
async def test_suche_mit_zeile_und_fehler():
    async with Client(mcp) as client:
        r = await client.call_tool(
            "search", {"pattern": "FREE_SHIPPING_FROM ="})
        assert ("bestellservice/shipping_costs.py:15:"
                in r.content[0].text)
        r = await client.call_tool("read_lines", {
            "path": "../.env", "start": 1, "end": 5})
        assert r.is_error
        assert "außerhalb" in r.content[0].text
