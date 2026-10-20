from compaction import MARK, compact, size

AUFTRAG = "Wo wird das Versandgewicht berechnet?"


def verlauf(schritte: int) -> list[dict]:
    msgs = [{"role": "system", "content": "SYS"},
            {"role": "user", "content": AUFTRAG}]
    for i in range(schritte):
        msgs.append({"role": "assistant", "content": "",
                     "tool_calls": [{"id": f"c{i}"}]})
        obs = ("FEHLER [not_found]: bestellservice/porto.py "
               "gibt es nicht" if i == 1 else
               f"bestellservice/labels.py:{i}: " + "x" * 400)
        msgs.append({"role": "tool", "content": obs,
                     "tool_call_id": f"c{i}"})
    return msgs


def fake_summary(prompt: str) -> str:
    fake_summary.calls += 1
    return "Gesucht nach Gewicht."


def test_unter_budget_keine_aenderung():
    fake_summary.calls = 0
    msgs = verlauf(2)
    assert compact(msgs, 10_000, fake_summary) is msgs
    assert fake_summary.calls == 0


def test_kopf_und_ende_bleiben_mitte_wird_markiert():
    fake_summary.calls = 0
    msgs = verlauf(8)
    neu = compact(msgs, 300, fake_summary, keep_last=3)
    assert fake_summary.calls == 1
    assert neu[:2] == msgs[:2]          # Auftrag wörtlich
    assert neu[-6:] == msgs[-6:]        # drei Schritte
    assert neu[2]["content"].startswith(MARK)
    assert size(neu) < size(msgs)


def test_pfade_und_fehler_ueberleben():
    neu = compact(verlauf(8), 300, fake_summary)
    text = neu[2]["content"]
    assert "bestellservice/porto.py" in text
    assert "FEHLER [not_found]" in text
    assert "bestellservice/labels.py" in text


def test_tool_paare_bleiben_zusammen():
    neu = compact(verlauf(8), 300, fake_summary)
    assert neu[3]["role"] == "assistant"


def test_laengere_zusammenfassung_wird_verworfen():
    msgs = verlauf(8)
    neu = compact(msgs, 300, lambda p: "bla " * 5000)
    assert neu is msgs
