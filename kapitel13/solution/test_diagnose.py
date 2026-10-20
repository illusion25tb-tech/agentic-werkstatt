"""Fixture-Traces: Testdaten, keine Messung."""
import json

from diagnose import diagnose


def t(tool, obs, **kw):
    return {"tool": tool, "args": {"path": "a.py"}, "obs": obs,
            **kw}


def bilder(recs):
    return [b for _, b, _ in diagnose(
        [json.dumps(r) for r in recs])]


def test_sauberer_trace_ohne_meldung():
    assert bilder([t("read_file", "1: x = 1"),
                   {"phase": "work", "peak_input": 2000},
                   t("search", "0 Treffer in 12 Dateien")]
                  ) == []


def test_leere_observation():
    assert bilder([t("read_file", "")]) == ["leere Observation"]


def test_wiederholung_ab_der_dritten():
    assert bilder([t("search", "x")] * 3) == [
        "Wiederholung ohne Fortschritt"]
    assert bilder([t("search", "x")] * 2) == []


def test_kontext_fast_voll():
    voll = {"phase": "work", "peak_input": 13_000}
    assert bilder([voll]) == ["Kontext fast voll"]


def test_timeout():
    obs = "FEHLER: TimeoutExpired: pytest nach 120 s"
    assert bilder([t("run_tests", obs)]) == ["Tool-Timeout"]


def test_policy_serie():
    p = "FEHLER [policy]: Bestehender Test: tabu"
    recs = [t("create_test", p), t("replace_in_file", p),
            t("create_test", p + " ")]
    assert bilder(recs) == ["Policy-Blockade in Serie"]


def test_freigabe_ohne_lesen():
    recs = [{"role": "orchestrator", "round": 1,
             "approve": True, "reason": "Setzt den Plan um."}]
    assert bilder(recs) == ["Freigabe ohne Lesen"]
    gelesen = [t("read_file", "1: x", role="reviewer",
                 round=1)] + recs
    assert bilder(gelesen) == []


def test_vertrag_verfehlt_in_serie():
    r = {"plan_rejected": ["tests/search.php"]}
    assert bilder([r, r]) == []
    assert bilder([r, r, r]) == ["Vertrag verfehlt in Serie"]
