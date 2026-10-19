"""Gliederung einer Python-Datei über das Modul ast."""
import ast
from pathlib import Path

from contracts import ToolError
from read_lines import im_repo

DEFS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def outline(path: str, root: Path) -> str:
    target = im_repo(path, root)
    if target.suffix != ".py" or not target.is_file():
        raise ToolError("invalid_args", f"{path}: outline nur "
                        "für .py-Dateien, sonst read_lines.")
    tree = ast.parse(target.read_text(encoding="utf-8"))
    out = []
    for node in tree.body:
        out += _eintrag(node)
        if isinstance(node, ast.ClassDef):
            for sub in node.body:
                out += _eintrag(sub, "    ")
    return "\n".join(out) or "(keine Definitionen)"


def _eintrag(node: ast.AST, indent: str = "") -> list[str]:
    if isinstance(node, ast.Assign):    # KONSTANTE = ...
        return [f"{indent}{node.lineno} {t.id}"
                for t in node.targets
                if isinstance(t, ast.Name) and t.id.isupper()]
    if not isinstance(node, DEFS):
        return []
    art = "class" if isinstance(node, ast.ClassDef) else "def"
    deko = "".join(f" @{ast.unparse(d)}"
                   for d in node.decorator_list)
    zeilen = f"{node.lineno}-{node.end_lineno}"
    return [f"{indent}{zeilen} {art} {node.name}{deko}"]
