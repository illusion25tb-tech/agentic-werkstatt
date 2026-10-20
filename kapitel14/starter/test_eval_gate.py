"""eval_gate mit Fixture-Reports und mit echten Reports."""
import copy
import json
from pathlib import Path

from eval_gate import gate, limits, mixed

HIER = Path(__file__).parent
CFG = HIER / "evals" / "baseline.json"
BASE = json.loads((HIER / "evals" / "baseline_report.json")
                  .read_text(encoding="utf-8"))


def write(tmp_path, **overall):
    rep = copy.deepcopy(BASE)
    rep["versions"]["harness"] = ["h1"]     # eine Version
    rep["overall"].update(overall)
    p = tmp_path / "report.json"
    p.write_text(json.dumps(rep), encoding="utf-8")
    return p


def test_gleich_wie_baseline_ist_gruen(tmp_path):
    assert gate(CFG, write(tmp_path)) == 0


def test_besser_ist_gruen(tmp_path):
    p = write(tmp_path, resolved=6, rate=0.4,
              ci95=[0.2, 0.64], tool_calls={"mean": 4.0,
                                            "stdev": 2.0})
    assert gate(CFG, p) == 0


def test_schlechter_ist_rot(tmp_path):
    p = write(tmp_path, policy=2, tests_changed=1)
    assert gate(CFG, p) == 1


def test_teurer_als_absolut_erlaubt():
    cur = dict(BASE["overall"], cost={"mean": 0.8,
                                      "stdev": 0.1})
    assert limits(cur, {"cost_mean": 0.5}) == [
        "Kosten je Run 0.8000 > 0.5 (absolut)"]


def test_gemischte_konfiguration_ist_kein_vergleich():
    assert mixed(BASE) == [
        "harness: 6262d83ca098, a90020737d8f"]
    assert gate(CFG, HIER / "evals/baseline_report.json") == 2


def test_echter_lauf_mit_rollen_ist_rot():
    """Kapitel 12: drei Rollen, policy 1 -> 2."""
    rep = HIER / "fixtures" / "report_rollen.json"
    assert gate(CFG, rep) == 1


def test_andere_aufgaben_kein_vergleich():
    rep = HIER / "fixtures" / "report_kap10.json"
    assert gate(CFG, rep) == 2
