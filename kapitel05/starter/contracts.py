"""Tool-Verträge: Schema, Fehlerklasse, Registry."""
from collections.abc import Callable
from dataclasses import dataclass

from pydantic import BaseModel, ValidationError

FEHLERART = {PermissionError: "permission",
             FileNotFoundError: "not_found",
             ValueError: "invalid_args"}


class ToolError(Exception):
    def __init__(self, kind: str, msg: str,
                 retryable: bool = False):
        super().__init__(msg)
        self.kind, self.retryable = kind, retryable

    def __str__(self) -> str:
        return f"FEHLER [{self.kind}]: {self.args[0]}"


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    args: type[BaseModel]       # mit extra="forbid"
    fn: Callable[..., str]
    read_only: bool = True
    idempotent: bool = True

    def schema(self) -> dict:
        return {"type": "function", "function": {
            "name": self.name,
            "description": self.description,
            "parameters": self.args.model_json_schema()}}

    def run(self, raw_args: dict | str) -> str:
        try:
            a = self.args.model_validate(raw_args)
        except ValidationError as e:
            err = e.errors()[0]
            feld = ".".join(map(str, err["loc"])) or "Objekt"
            raise ToolError("invalid_args",
                            f"Feld {feld!r}: {err['msg']}")
        try:
            return self.fn(**a.model_dump())
        except ToolError:
            raise
        except Exception as e:  # noqa: BLE001
            kind = next((k for t, k in FEHLERART.items()
                         if isinstance(e, t)), "failed")
            raise ToolError(kind, f"{type(e).__name__}: {e}")


class Registry:
    """Was hier nicht drinsteht, sieht das Modell nicht."""

    def __init__(self, specs: list[ToolSpec]):
        self.specs = {s.name: s for s in specs}

    def schemas(self) -> list[dict]:
        return [s.schema() for s in self.specs.values()]

    def call(self, name: str, args: dict | str) -> str:
        spec = self.specs.get(name)
        if spec is None:
            raise ToolError(
                "unknown_tool", f"{name!r} gibt es nicht. "
                "Verfügbar: " + ", ".join(self.specs))
        return spec.run(args)
