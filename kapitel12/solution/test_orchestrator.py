"""Ablauf mit einem geskripteten Modell pro Rolle."""
import json
import sys

from conftest import git, j, skript
from orchestrator import Orchestrator

V = "bestellservice/versand.py"
L = "bestellservice/labels.py"
TICKET = "Label für 38 kg hat den Standardtarif."
PLAN = j(steps=["Rückfall über 31,5 kg auf SPERRGUT"],
         files=[V], acceptance=["38 kg ist SPERRGUT"])
FIX = ("replace_in_file", {"path": V,
                           "old": '    return "XL"\n',
                           "new": '    return "SPERRGUT"\n'})
NEU = ("from bestellservice.versand import klasse\n\n\n"
       "def test_38_kg():\n"
       '    assert klasse(38.0) == "SPERRGUT"\n')
TEST = ("create_test", {"path": "tests/test_grenze.py",
                        "content": NEU})
RUN = ("run_tests", {"target": "tests"})


def verdict(approve, path="tests", line=0, quote="passed"):
    return j(approve=approve, reason="-", evidence=[
        {"path": path, "line": line, "quote": quote}])


OK = verdict(True, V, 8, 'return "SPERRGUT"')


def orchestrate(repo, tmp_path, **models):
    o = Orchestrator(TICKET, "NL-900", repo, models,
                     sys.executable, tmp_path)
    code = o.run()
    lines = o.trace.read_text("utf-8").splitlines()
    return code, [json.loads(z) for z in lines]


def test_freigabe_mit_beleg(repo, tmp_path):
    seen = []
    code, trace = orchestrate(
        repo, tmp_path,
        planner=skript(("read_file", {"path": V}),
                       "Rückfall auf XL in Zeile 8.", PLAN),
        coder=skript(FIX, TEST, RUN, "Fertig."),
        reviewer=skript("Zeile 8 gibt SPERRGUT.", OK,
                        seen=seen))
    assert code == 0
    assert "SPERRGUT" in (repo / V).read_text()  # in main
    assert "coder-NL-900" not in git(repo, "worktree", "list")
    rollen = {r.get("role") for r in trace}
    assert rollen >= {"planner", "coder", "tester",
                      "reviewer", "orchestrator"}
    gesehen = str(seen[0])          # erster Request
    assert TICKET in gesehen and "git diff" in gesehen
    assert "Rückfall über 31,5 kg" not in gesehen  # kein Plan


def test_freigabe_ohne_beleg_wird_abgelehnt(repo, tmp_path):
    nur_tests = verdict(True)       # "passed", keine Zeile
    code, trace = orchestrate(
        repo, tmp_path,
        planner=skript("Ursache gefunden.", PLAN),
        coder=skript(FIX, TEST, RUN, "Fertig."),
        reviewer=skript("Alles grün.", *[nur_tests] * 5))
    assert code == 2
    text = json.dumps(trace, ensure_ascii=False)
    assert "Eine Freigabe braucht einen Beleg" in text
    assert "UnexpectedModelBehavior" in trace[-1]["abort"]
    assert "SPERRGUT" not in (repo / V).read_text()


def test_zwei_ablehnungen_enden_beim_menschen(repo, tmp_path):
    nein = verdict(False, V, 4, "def klasse")
    code, trace = orchestrate(
        repo, tmp_path,
        planner=skript("Ursache gefunden.", PLAN),
        coder=skript(FIX, TEST, RUN, "Fertig.",
                     ("create_test", {
                         "path": "tests/test_zwei.py",
                         "content": NEU}), RUN, "Fertig."),
        reviewer=skript("Nein.", nein, "Wieder nein.", nein))
    assert code == 2
    assert trace[-1]["abort"] == ("Stop: 2 Runden ohne "
                                  "Freigabe")
    assert "SPERRGUT" not in (repo / V).read_text()
    assert "NL-900: nicht freigegeben" in git(
        repo, "log", "--oneline", "coder/NL-900")


def test_falsche_datei_im_plan(repo, tmp_path):
    """Kaskade: Planner nennt labels.py, Coder folgt treu.
    Der Reviewer sieht das Ticket, nicht den Plan."""
    falsch = j(steps=["Label korrigieren"], files=[L],
               acceptance=["38 kg"])
    nein = verdict(False, V, 8, 'return "XL"')
    code, trace = orchestrate(
        repo, tmp_path,
        planner=skript("Liegt am Label.", falsch),
        coder=skript(
            ("replace_in_file", {"path": L, "old": "PF-",
                                 "new": "PF-X-"}),
            RUN, "Fertig.", FIX, RUN, "Fertig."),
        reviewer=skript(("read_file", {"path": V}),
                        "Ursache liegt in versand.py.", nein))
    assert code == 2
    assert "Fremde Dateien" in trace[-1]["abort"]
    assert git(repo, "diff", "HEAD") == ""      # main sauber


def test_gesamtbudget(repo, tmp_path):
    suche = ("search", {"pattern": "kg"})
    code, trace = orchestrate(
        repo, tmp_path, planner=skript(*[suche] * 13))
    assert code == 2
    assert trace[-1]["abort"].startswith("UsageLimitExceeded")
    phase = [r for r in trace if r.get("phase") == "work"]
    assert phase[0]["role"] == "planner"
