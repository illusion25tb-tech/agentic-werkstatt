from pseudonym import scrub

KEY = b"testschluessel"
SPAN = {"werkstatt.user": "deniz.arslan",
        "gen_ai.input.messages": "Kundin Erika Muster ...",
        "gen_ai.tool.name": "read_file",
        "werkstatt.note": "Bearer abcdefghijklmnop1234"}


def test_gleiche_kennung_gleiches_pseudonym():
    a = scrub(SPAN, KEY, environ={})
    b = scrub(SPAN, KEY, environ={})
    assert a["werkstatt.user"] == b["werkstatt.user"]
    assert "deniz" not in str(a)


def test_anderer_schluessel_anderes_pseudonym():
    a = scrub(SPAN, KEY, environ={})
    b = scrub(SPAN, b"anderer", environ={})
    assert a["werkstatt.user"] != b["werkstatt.user"]


def test_inhalt_nur_per_opt_in():
    assert "gen_ai.input.messages" not in scrub(
        SPAN, KEY, environ={})
    mit = scrub(SPAN, KEY,
                environ={"WERKSTATT_TRACE_CONTENT": "1"})
    assert "Erika" in mit["gen_ai.input.messages"]


def test_secrets_geschwaerzt_wie_kapitel_11():
    out = scrub(SPAN, KEY, environ={})
    assert out["werkstatt.note"] == "Bearer [SECRET]"
    assert out["gen_ai.tool.name"] == "read_file"
