"""MCP-Server aus Kapitel 5, jetzt mit den Grounding-Tools."""
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

import contracts
from tools import GROUNDING

READ_ONLY = ToolAnnotations(
    read_only_hint=True, destructive_hint=False,
    idempotent_hint=True, open_world_hint=False)

mcp = MCPServer("repo")


def _call(name: str, **args) -> str:
    """Dieselbe Prüfung wie lokal: Vertrag aus tools.py."""
    try:
        return GROUNDING.call(name, args)
    except contracts.ToolError as e:
        raise ToolError(str(e)) from None   # Text fürs Modell


@mcp.tool(annotations=READ_ONLY)
def search(pattern: str, path: str = ".") -> str:
    """Sucht pattern (Regex), liefert Datei:Zeile: Text."""
    return _call("search", pattern=pattern, path=path)


@mcp.tool(annotations=READ_ONLY)
def read_lines(path: str, start: int, end: int) -> str:
    """Liest Zeilen start bis end mit Nummern, max. 60."""
    return _call("read_lines", path=path, start=start, end=end)


@mcp.tool(annotations=READ_ONLY)
def outline(path: str) -> str:
    """Gliederung einer .py-Datei mit Zeilen."""
    return _call("outline", path=path)


if __name__ == "__main__":
    mcp.run()
