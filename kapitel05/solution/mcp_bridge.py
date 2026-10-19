"""MCP-Clients als Toolbox für agent_fc.py."""
import json
import sys
from contextlib import ExitStack, contextmanager

import jsonschema
from anyio.from_thread import start_blocking_portal
from mcp import Client, StdioServerParameters

from allowlist import PINS, check
from contracts import ToolError


class Bridge:
    def __init__(self, portal):
        self.portal = portal
        self.tools = {}               # Name -> (Client, Tool)

    def schemas(self) -> list[dict]:
        return [{"type": "function", "function": {
            "name": t.name, "description": t.description or "",
            "parameters": t.input_schema}}
            for _, t in self.tools.values()]

    def call(self, name: str, args: dict | str) -> str:
        if name not in self.tools:
            raise ToolError("unknown_tool", f"{name!r} gibt es "
                            "nicht. Verfügbar: " + ", ".join(
                                self.tools))
        client, tool = self.tools[name]
        try:
            jsonschema.validate(args, tool.input_schema)
        except jsonschema.ValidationError as e:
            raise ToolError("invalid_args", e.message) from None
        res = self.portal.call(client.call_tool, name, args)
        text = "\n".join(c.text for c in res.content
                         if c.type == "text")
        if res.is_error:
            raise ToolError("server", text)
        return text[:4000]


def _server(target):
    if isinstance(target, str):       # Pfad zu einem Skript
        return StdioServerParameters(command=sys.executable,
                                     args=[target])
    return target                     # Serverobjekt (Tests)


@contextmanager
def connect(*targets, pins: dict | None = None, log=print):
    with start_blocking_portal() as portal, ExitStack() as st:
        bridge = Bridge(portal)
        for target in targets:
            client = Client(_server(target))
            c = st.enter_context(
                portal.wrap_async_context_manager(client))
            # ohne Paginierung: genügt für kleine Server
            tools = portal.call(c.list_tools).tools
            if pins is not None:
                tools, rejected = check(tools, pins)
                for name, grund in rejected:
                    log(f"Tool {name!r} abgelehnt: {grund}")
            for t in tools:
                if t.name in bridge.tools:  # nie überschreiben
                    log(f"Tool {t.name!r} doppelt, verworfen")
                    continue
                bridge.tools[t.name] = (c, t)
        yield bridge


def list_tools(target) -> list:
    with connect(target) as bridge:
        return [t for _, t in bridge.tools.values()]


if __name__ == "__main__":
    import agent_fc
    pins = None
    if PINS.exists():
        pins = json.loads(PINS.read_text(encoding="utf-8"))
    with connect("repo_server.py", pins=pins) as bridge:
        print(agent_fc.run(" ".join(sys.argv[1:]), bridge))
