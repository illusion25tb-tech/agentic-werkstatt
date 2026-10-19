"""Erste Grounding-Tools: Suche und Zeilenbereiche."""
import os
from functools import partial
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from contracts import Registry, ToolSpec
from read_lines import read_lines
from search_rg import search

ROOT = Path(os.environ.get(
    "REPO_ROOT", Path(__file__).parents[2] / "bestellservice"
)).resolve()


class Args(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SearchArgs(Args):
    pattern: str = Field(
        min_length=3, max_length=100,
        description="Regex, z. B. def .*weight")
    path: str = Field(".", description="Ordner oder Datei")


class LinesArgs(Args):
    path: str = Field(
        description="z. B. bestellservice/cart.py")
    start: int = Field(ge=1)
    end: int = Field(ge=1, description="höchstens start+59")


GROUNDING = Registry([
    ToolSpec("search", "Sucht pattern (Regex, ohne Groß/"
             "klein) in Dateien unter path. Liefert "
             "Datei:Zeile: Text, höchstens 30 Treffer. 'Keine "
             "Treffer' ist ein Ergebnis.",
             SearchArgs, partial(search, root=ROOT)),
    ToolSpec("read_lines", "Liest Zeilen start bis end einer "
             "Datei mit Zeilennummern, höchstens 60. Fehler "
             "invalid_args nennt die Zeilenzahl.",
             LinesArgs, partial(read_lines, root=ROOT)),
])
