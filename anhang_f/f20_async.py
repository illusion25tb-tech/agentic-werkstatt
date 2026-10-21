"""async und await: warten, ohne zu blockieren."""

import asyncio


async def call_tool(name: str, seconds: float) -> str:
    await asyncio.sleep(seconds)  # steht für Netzwerk-I/O
    return f"{name}: fertig"


async def main() -> None:
    print(await call_tool("read_file", 0.01))
    both = await asyncio.gather(
        call_tool("search", 0.05),
        call_tool("list_files", 0.01),
    )
    print(both)


asyncio.run(main())
