"""Read-only MCP-Server über einem Repository-Checkout."""
import os
from pathlib import Path

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from tools import _im_workspace  # Pfadprüfung, Kapitel 4

ROOT = Path(os.environ.get(
    "REPO_ROOT", Path(__file__).parents[2] / "bestellservice"
)).resolve()
READ_ONLY = ToolAnnotations(
    read_only_hint=True, destructive_hint=False,
    idempotent_hint=True, open_world_hint=False)
SKIP = {".git", ".venv", "__pycache__", ".pytest_cache"}

mcp = MCPServer("repo")


def _pfad(path: str) -> Path:
    try:
        return _im_workspace(path, ROOT)
    except PermissionError as e:
        raise ToolError(str(e)) from None   # Text fürs Modell


def _dateien(path: str) -> list[Path]:
    base = _pfad(path)
    if not base.is_dir():
        raise ToolError(f"{path!r} ist kein Verzeichnis.")
    return sorted(p for p in base.rglob("*") if p.is_file()
                  and not SKIP & set(p.parts))


@mcp.tool(annotations=READ_ONLY)
def list_files(path: str = ".") -> str:
    """Listet Dateien unter path, höchstens 200."""
    files = [p.relative_to(ROOT).as_posix()
             for p in _dateien(path)]
    return "\n".join(files[:200]) or "(leer)"


@mcp.tool(annotations=READ_ONLY)
def read_file(path: str) -> str:
    """Liest eine Textdatei, höchstens 4.000 Zeichen."""
    target = _pfad(path)
    if not target.is_file():
        raise ToolError(f"{path} gibt es nicht. list_files "
                        "zeigt vorhandene Dateien.")
    return target.read_text(encoding="utf-8")[:4000]


@mcp.tool(annotations=READ_ONLY)
def search(text: str, path: str = ".") -> str:
    """Nennt Dateien, die text enthalten, höchstens 50."""
    if len(text) < 3:
        raise ToolError("Suchtext: mindestens 3 Zeichen.")
    hits = []
    for p in _dateien(path):
        inhalt = p.read_text(encoding="utf-8", errors="ignore")
        if text.lower() in inhalt.lower():
            hits.append(p.relative_to(ROOT).as_posix())
    return "\n".join(hits[:50]) or "Keine Treffer."


if __name__ == "__main__":
    mcp.run()                       # Standard-Transport: stdio
