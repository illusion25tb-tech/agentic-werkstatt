from policy import Policy, Risk


def nie(*a):
    raise AssertionError("Hier darf niemand gefragt werden")


def test_lesen_ohne_rueckfrage():
    p = Policy()
    assert p.check("read_file", {"path": "a"}, nie) is None


def test_schreiben_fragt_und_ablehnung_blockiert():
    fragen = []
    p = Policy()
    grund = p.check("replace_in_file", {"path": "x.py"},
                    lambda *a: fragen.append(a) or False)
    assert fragen and fragen[0][0] is Risk.WRITE
    assert "abgelehnt" in grund


def test_push_pr_loeschen_deploy_gibt_es_nicht():
    for tool in ("git_push", "open_pr", "delete_file",
                 "deploy"):
        assert "kein Werkzeug" in Policy().check(tool, {}, nie)


def test_bestehender_test_ist_eigene_klasse():
    p = Policy(protected={"tests/test_a.py"})
    fragen = []
    p.check("replace_in_file", {"path": "tests/test_a.py"},
            lambda r, *a: fragen.append(r) or True)
    assert fragen == [Risk.PROTECTED]


def test_eval_zaehlt_statt_zu_fragen():
    p = Policy("eval", {"tests/test_a.py"})
    assert p.check("replace_in_file", {"path": "b.py"}, nie) \
        is None
    assert "tabu" in p.check(
        "replace_in_file", {"path": "tests/test_a.py"}, nie)
    assert p.asked == {"schreiben": 1, "testdatei": 1}


def test_nur_lesen_sperrt_tests_und_schreiben():
    p = Policy("nur_lesen")
    assert p.check("search", {}, nie) is None
    assert "nur_lesen" in p.check("run_tests", {}, nie)
