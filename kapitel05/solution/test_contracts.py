import pytest

from contracts import ToolError
from tools import ALL, TOOLS


def test_schema_ist_streng():
    p = TOOLS.specs["read_file"].schema()["function"]
    params = p["parameters"]
    assert params["required"] == ["path"]
    assert params["additionalProperties"] is False


def test_unbekanntes_argument_ist_toolerror():
    with pytest.raises(ToolError) as e:
        TOOLS.call("read_file", {"path": "x", "mode": "w"})
    assert e.value.kind == "invalid_args"


def test_falscher_typ_und_kein_json():
    for args in ({"path": ["a", "b"]}, '{"path": "a"'):
        with pytest.raises(ToolError) as e:
            TOOLS.call("read_file", args)
        assert e.value.kind == "invalid_args"


def test_pfad_ausserhalb_ist_permission():
    for p in ["../tools.py", "/etc/hosts",
              "C:/Windows/win.ini"]:
        with pytest.raises(ToolError) as e:
            TOOLS.call("read_file", {"path": p})
        assert e.value.kind == "permission", p
        assert "PermissionError" in str(e.value)


def test_datei_fehlt_ist_not_found():
    with pytest.raises(ToolError) as e:
        TOOLS.call("read_file",
                   {"path": "bestellung_4711.json"})
    assert e.value.kind == "not_found"
    assert "list_files" in str(e.value)


def test_unbekanntes_tool_nennt_verfuegbare():
    with pytest.raises(ToolError, match="read_file") as e:
        TOOLS.call("write_file", {})
    assert e.value.kind == "unknown_tool"


def test_git_schema_kennt_nur_lesende_befehle():
    p = TOOLS.specs["git"].schema()["function"]["parameters"]
    enum = p["properties"]["subcommand"]["enum"]
    assert "commit" not in enum and "log" in enum
    for args in ({"subcommand": "push"},
                 {"command": "log -3"},
                 {"subcommand": "log", "args": "-3"}):
        with pytest.raises(ToolError) as e:
            TOOLS.call("git", args)
        assert e.value.kind == "invalid_args", args


def test_git_optionen_weiter_per_allowlist():
    for opt in ["--output=x.txt", "-nOevil", "--no-index"]:
        with pytest.raises(ToolError) as e:
            TOOLS.call("git", {"subcommand": "log",
                               "args": [opt]})
        assert e.value.kind == "permission", opt


def test_rechner_und_fehlerart_failed():
    summe = TOOLS.call("calculator",
                       {"expression": "2*89.90 + 3*12.50"})
    assert summe == "217.3"
    with pytest.raises(ToolError) as e:
        TOOLS.call("calculator", {"expression": "1/0"})
    assert e.value.kind == "failed"


def test_registry_filtert_nach_rechten():
    assert all(s.read_only for s in ALL)
    assert set(TOOLS.specs) == {s.name for s in ALL}
