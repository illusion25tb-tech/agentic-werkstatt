"""Lesende Tools des Butlers. Sie kennen kein Framework."""
from deps import Deps
from read_lines import im_repo, read_lines
from search_rg import search as rg_search
from search_rg import walk


def list_files(deps: Deps, path: str = ".") -> str:
    """Listet Dateien unter path, z. B. "." oder "tests"."""
    base = im_repo(path, deps.repo)
    if not base.exists():
        raise FileNotFoundError(
            f"{path} gibt es nicht. list_files('.') zeigt "
            "alle Dateien.")
    files = [rel for _, rel in walk(base, deps.repo)]
    return "\n".join(files[:200]) or "(leer)"


def read_file(deps: Deps, path: str, start: int = 1,
              end: int = 60) -> str:
    """Liest Zeilen start bis end einer Datei mit Nummern,
    höchstens 60 Zeilen je Aufruf."""
    return read_lines(path, start, end, deps.repo)


def search(deps: Deps, pattern: str, path: str = ".") -> str:
    """Sucht pattern (Regex, ohne Groß/klein) unter path.
    Liefert Datei:Zeile: Text, höchstens 30 Treffer."""
    return rg_search(pattern, path, deps.repo)
