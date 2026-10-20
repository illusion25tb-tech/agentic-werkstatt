import json

import pytest

import agent
from budget import BudgetExceeded, RunBudget

PREISE = {"models": {"m": {"input": 2.0, "output": 10.0}}}


def j(tool, **args):
    return json.dumps({"thought": "-", "tool": tool,
                       "args": args})


def test_bricht_genau_beim_ueberschreiten_ab(monkeypatch,
                                             tmp_path):
    # jede Antwort: 10.000 + 1.000 Token = 0,03 je Aufruf
    def ask(messages):
        agent.LAST_USAGE.clear()
        agent.LAST_USAGE.update(prompt_tokens=10_000,
                                completion_tokens=1_000)
        return j("calculator", expression=str(len(messages)))
    monkeypatch.setattr(agent, "TRACE", tmp_path / "t.jsonl")
    monkeypatch.setattr(agent, "ask_model", ask)
    b = RunBudget("m", max_cost=0.10, max_seconds=60,
                  prices=PREISE)
    assert agent.run("x", b) == "ABBRUCH: cost_budget"
    assert b.spent == pytest.approx(0.12)   # 4 Aufrufe
    letzte = (tmp_path / "t.jsonl").read_text().splitlines()[-1]
    assert json.loads(letzte)["abort"] == "cost_budget"


def test_schaetzung_vor_dem_aufruf():
    b = RunBudget("m", max_cost=0.001, max_seconds=60,
                  prices=PREISE)
    riesig = [{"role": "user", "content": "x" * 4_000_000}]
    with pytest.raises(BudgetExceeded) as e:
        b.check_before(riesig)      # ~1 Mio. Token: 2,00
    assert e.value.reason == "cost_budget"
    assert b.spent == 0             # nichts ausgegeben


def test_zeitlimit_mit_gefaelschter_uhr():
    t = iter([0.0, 301.0])
    b = RunBudget("m", max_cost=1.0, max_seconds=300,
                  prices=PREISE, clock=lambda: next(t))
    with pytest.raises(BudgetExceeded) as e:
        b.check_before([])
    assert e.value.reason == "time_budget"


def test_unbekannter_preis_ist_kein_null():
    with pytest.raises(ValueError):
        RunBudget("gibt-es-nicht", 0.5, 60, prices=PREISE)


def test_preise_aus_kapitel_10():
    b = RunBudget("llama3.2-16k", 0.5, 60)   # prices.toml
    assert b.cost(1_000_000, 1_000_000) == 0.0
