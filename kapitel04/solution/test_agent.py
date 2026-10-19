import json

import agent


def scripted(*antworten):
    it = iter(antworten)
    return lambda messages: next(it)


def j(tool, **args):
    d = {"thought": "-", "tool": tool, "args": args}
    return json.dumps(d)


def test_happy_path(monkeypatch, tmp_path):
    monkeypatch.setattr(agent, "TRACE", tmp_path / "t.jsonl")
    monkeypatch.setattr(agent, "ask_model", scripted(
        j("read_file", path="bestellungen/4711.json"),
        j("calculator", expression="2*89.90 + 3*12.50"),
        j("finish", answer="217.3")))
    assert agent.run("Gesamtwert 4711?") == "217.3"


def test_step_budget(monkeypatch, tmp_path):
    # wechselnde Aktionen: keine Wiederholung, nur das Budget greift
    monkeypatch.setattr(agent, "TRACE", tmp_path / "t.jsonl")
    n = iter(range(100))
    monkeypatch.setattr(agent, "ask_model", lambda m: j(
        "calculator", expression=str(next(n))))
    assert agent.run("x") == "ABBRUCH: Step-Budget erschöpft"


def test_pfad_ausserhalb():
    d = agent.Decision(thought="", tool="read_file",
                       args={"path": "../agent.py"})
    assert "PermissionError" in agent.execute(d)


def test_kein_json(monkeypatch, tmp_path):
    monkeypatch.setattr(agent, "TRACE", tmp_path / "t.jsonl")
    monkeypatch.setattr(agent, "ask_model", scripted(
        "Ich lese jetzt die Datei.", j("finish", answer="ok")))
    assert agent.run("x") == "ok"


def test_repeat_abbruch(monkeypatch, tmp_path):
    monkeypatch.setattr(agent, "TRACE", tmp_path / "t.jsonl")
    calls = []
    def m(messages):
        calls.append(1)
        return j("read_file", path="4711.json")
    monkeypatch.setattr(agent, "ask_model", m)
    assert agent.run("x") == "ABBRUCH: Wiederholung ohne Fortschritt"
    assert len(calls) == 3


def test_list_files():
    from tools import list_files
    assert "bestellungen/4711.json" in list_files(".")


def test_absolute_pfade():
    for p in ["../tools.py", "/etc/hosts", "C:/Windows/win.ini"]:
        d = agent.Decision(thought="", tool="read_file",
                           args={"path": p})
        assert "PermissionError" in agent.execute(d), p


def test_repeat_nur_direkt_hintereinander(monkeypatch, tmp_path):
    monkeypatch.setattr(agent, "TRACE", tmp_path / "t.jsonl")
    calc = j("calculator")             # fehlendes Argument
    monkeypatch.setattr(agent, "ask_model", scripted(
        calc, calc, j("list_files", path="."), calc,
        j("finish", answer="ok")))
    assert agent.run("x") == "ok"


def test_fehlendes_feld_wird_benannt(monkeypatch, tmp_path):
    monkeypatch.setattr(agent, "TRACE", tmp_path / "t.jsonl")
    seen = []
    def m(messages):
        seen.append(messages[-1]["content"])
        if len(seen) == 1:
            return '{"tool": "finish", "args": {}}'
        return j("finish", answer="ok")
    monkeypatch.setattr(agent, "ask_model", m)
    assert agent.run("x") == "ok"
    assert "'thought'" in seen[1]


def test_list_files_falsches_verzeichnis():
    from tools import list_files
    import pytest
    with pytest.raises(FileNotFoundError, match="ohne"):
        list_files("workspace/")


def test_repeat_auch_bei_ungueltiger_antwort(monkeypatch, tmp_path):
    monkeypatch.setattr(agent, "TRACE", tmp_path / "t.jsonl")
    calls = []
    def m(messages):
        calls.append(1)
        return '{"tool": "finish", "args": {"answer": "x"}}'
    monkeypatch.setattr(agent, "ask_model", m)
    assert agent.run("x").startswith("ABBRUCH: Wiederholung")
    assert len(calls) == 3


def test_git_sperrt_schreibende_befehle():
    import pytest
    import tools
    for cmd in ["commit -am x", "push", "checkout main",
                "log --output=x.txt", "grep -Ovim x",
                "-c core.pager=evil log", "grep -nOevil x",
                "diff --no-index a b", "show --ext-diff"]:
        with pytest.raises(PermissionError):
            tools.git(cmd)


def test_git_liest_repository(monkeypatch, tmp_path):
    import subprocess
    import tools
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "a.txt").write_text("hallo\n", encoding="utf-8")
    for a in (["init", "-q"], ["add", "."],
              ["commit", "-q", "-m", "Erster Commit"]):
        subprocess.run(["git", "-c", "user.name=t",
                        "-c", "user.email=t@t", *a],
                       cwd=ws, check=True)
    monkeypatch.setattr(tools, "WORKDIR", ws)
    assert "Erster Commit" in tools.git("log --oneline -1")
    assert "a.txt" in tools.git("grep -l hallo")
    assert "Erster" in tools.git("log --format=%s -1")
