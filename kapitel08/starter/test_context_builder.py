from context_builder import MEM_HEAD, build, est, inventory

EP = {"id": 1, "created": "2026-10-19", "verified": True,
      "source": "Run mo-A1", "lesson": "Gewicht: labels.py 45"}


def test_reihenfolge_und_kennzeichnung():
    msgs = build("SYS", "Tests: pytest", [EP], "Frage?")
    assert [m["role"] for m in msgs] == ["system", "system",
                                         "user"]
    assert "AGENTS.md" in msgs[0]["content"]
    assert msgs[1]["content"].startswith(MEM_HEAD)
    assert "[E1, 2026-10-19, verifiziert" in msgs[1]["content"]
    assert msgs[2]["content"] == "Frage?"


def test_ohne_erinnerungen_kein_block():
    msgs = build("SYS", "", [], "Frage?")
    assert len(msgs) == 2
    assert MEM_HEAD not in str(msgs)


def test_budget_schneidet_erinnerungen_zuerst():
    viele = [dict(EP, id=i, lesson="x" * 400)
             for i in range(10)]
    msgs = build("SYS", "", viele, "Frage?", budget=400)
    block = msgs[1]["content"]
    assert "[E0," in block and "[E9," not in block
    assert est("".join(m["content"] for m in msgs)) <= 400


def test_inventur_nach_herkunft():
    msgs = build("S" * 40, "", [EP], "A" * 40)
    msgs += [{"role": "assistant", "content": "",
              "tool_calls": [{"id": "c1"}]},
             {"role": "tool", "content": "O" * 400},
             {"role": "user", "content": "Antwort abgelehnt"}]
    inv = inventory(msgs)
    assert inv["auftrag"] == 10
    assert inv["observations"] == 100
    assert inv["memory"] > 0 and inv["harness"] > 0
