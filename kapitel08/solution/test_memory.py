from datetime import date

from memory import open_db, recall, record

HEUTE = date(2026, 10, 20)


def db_mit_drei():
    conn = open_db()
    record(conn, "Labelgewicht finden",
           ["bestellservice/labels.py"], "ok",
           "_parcel_weight in labels.py Zeile 45", "Run 1",
           verified=True, today=HEUTE)
    record(conn, "Rechnungsnummer",
           ["bestellservice/invoice.py"], "ok",
           "invoice_number baut RE-Jahr-Id", "Run 2",
           verified=True, today=HEUTE)
    record(conn, "Labeltext", ["bestellservice/labels.py"],
           "ok", "render baut den Labeltext", "Run 3",
           verified=True, days=1, today=HEUTE)
    return conn


def test_abruf_nach_dateiueberlappung():
    conn = db_mit_drei()
    treffer = recall(conn, "Frage",
                     files=["bestellservice/labels.py"],
                     today=HEUTE)
    assert [e["source"] for e in treffer] == ["Run 3", "Run 1"]


def test_abruf_nach_worten_und_top_k():
    conn = db_mit_drei()
    treffer = recall(conn, "Wie entsteht die Rechnungsnummer?",
                     today=HEUTE, k=1)
    assert [e["source"] for e in treffer] == ["Run 2"]
    assert treffer[0]["files"] == ["bestellservice/invoice.py"]


def test_abgelaufen_kommt_nicht_zurueck():
    conn = db_mit_drei()
    spaeter = date(2026, 10, 25)
    treffer = recall(conn, "Labeltext labels.py",
                     files=["bestellservice/labels.py"],
                     today=spaeter)
    assert "Run 3" not in [e["source"] for e in treffer]


def test_ohne_ueberlappung_nichts():
    assert recall(db_mit_drei(), "Gutschein", today=HEUTE) == []
