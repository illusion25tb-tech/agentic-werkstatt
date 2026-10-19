import streuung


def test_zaehlt_antworten(monkeypatch):
    antworten = iter(["hoch", "mittel", "hoch", "hoch",
                      "Das hängt\n davon ab."])
    monkeypatch.setattr(streuung, "ask_model",
                        lambda messages: next(antworten))
    c = streuung.streuung("Ticket", n=5)
    assert c["hoch"] == 3
    assert c["Das hängt davon ab."] == 1   # Leerraum normiert
    assert sum(c.values()) == 5
