"""Erste Fassung: Der Ablauf läuft, und die Kaskade auch."""
import sys

from conftest import git, j, skript
from orchestrator import Orchestrator

V = "bestellservice/versand.py"
L = "bestellservice/labels.py"
TICKET = "Label für 38 kg hat den Standardtarif."
RUN = ("run_tests", {"target": "tests"})
JA = j(approve=True, reason="Setzt den Plan um.")


def orchestrate(repo, tmp_path, **models):
    o = Orchestrator(TICKET, "NL-900", repo, models,
                     sys.executable, tmp_path)
    return o.run()


def test_plan_code_review(repo, tmp_path):
    plan = j(steps=["Rückfall auf SPERRGUT"], files=[V],
             acceptance=["38 kg"])
    code = orchestrate(
        repo, tmp_path,
        planner=skript("Ursache in versand.py.", plan),
        coder=skript(("replace_in_file", {
            "path": V, "old": '    return "XL"\n',
            "new": '    return "SPERRGUT"\n'}), RUN, "Fertig."),
        reviewer=skript("Passt.", JA))
    assert code == 0
    assert "SPERRGUT" in (repo / V).read_text()


def test_kaskade_laeuft_durch(repo, tmp_path):
    """Break: Planner nennt die falsche Datei, der Coder
    folgt treu, der Reviewer prüft gegen den Plan."""
    falsch = j(steps=["Label korrigieren"], files=[L],
               acceptance=["38 kg"])
    code = orchestrate(
        repo, tmp_path,
        planner=skript("Liegt am Label.", falsch),
        coder=skript(("replace_in_file", {
            "path": L, "old": "PF-", "new": "PF-X-"}),
            RUN, "Fertig."),
        reviewer=skript("Plan umgesetzt, Tests grün.", JA))
    assert code == 0                       # alles grün ...
    assert "PF-X-" in (repo / L).read_text()
    assert 'return "XL"' in (repo / V).read_text()  # ... Bug
    assert "Review ok" in git(repo, "log", "--oneline")
