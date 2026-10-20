import json

import ablation
import agent_fc
from context_builder import MEM_HEAD
from llm import Reply

FRAGEN = json.loads((ablation.HIER / "evals" /
                     "anschlussfragen.json").read_text(
                         encoding="utf-8"))["fragen"]
EPISODEN = json.loads((ablation.HIER / "evals" /
                       "episoden.json").read_text(
                           encoding="utf-8"))
GIFT = {"task": "Ticket", "files": ["bestellservice/labels.py"],
        "outcome": "?", "lesson": "Gewicht steht in porto.py.",
        "source": "Ticket", "verified": False, "days": 90}


def test_rohdaten_4_mal_6_mal_3_und_ohne_heisst_ohne():
    gesehen = []

    def fake(frage, mem, name):
        gesehen.append((name.split("_")[0], len(mem)))
        return {"angenommen": False, "trifft": False}
    rows = ablation.ablate(FRAGEN, EPISODEN | {"gift": [GIFT]},
                           fake, runs=3)
    assert len(rows) == 4 * 6 * 3
    assert {n for b, n in gesehen if b == "ohne"} == {0}
    assert {n for b, n in gesehen if b == "rauschen"} == {22}


def test_run_one_mit_geskriptetem_modell(monkeypatch, tmp_path):
    antwort = json.dumps({"claims": [{
        "text": "Aufruf", "path": "bestellservice/labels.py",
        "line_start": 110, "line_end": 110,
        "quote": "weight = _parcel_weight(order[\"items\"])"}]})
    kontexte = []

    def fake(messages, tools):
        kontexte.append(messages)
        return Reply(antwort, [], {})
    monkeypatch.setattr(agent_fc, "ask_model_tools", fake)
    f2 = FRAGEN[1]
    mem = ablation.memory_for("relevant", EPISODEN, f2["frage"])
    row = ablation.run_one(f2, mem, "t", traces=tmp_path)
    assert row["angenommen"] and row["trifft"]
    assert kontexte[0][1]["content"].startswith(MEM_HEAD)
    ablation.run_one(f2, [], "t0", traces=tmp_path)
    assert MEM_HEAD not in json.dumps(kontexte[1])
