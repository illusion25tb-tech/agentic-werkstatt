import pytest

from conftest import KEY
from taint_policy import TaintPolicy, verdict


def nie(*a):
    raise AssertionError("Hier darf niemand gefragt werden")


@pytest.mark.parametrize("tool, args, tainted, erwartet", [
    ("read_file", {"path": "README.md"}, True, "allow"),
    ("read_file", {"path": ".env"}, False, "deny"),
    ("read_file", {"path": "..\\conf\\.env.local"}, False,
     "deny"),
    ("create_test", {"path": "tests/test_a.py"}, False,
     "allow"),
    ("create_test", {"path": "tests/test_a.py"}, True,
     "approve"),
    ("create_test", {"content": f"# {KEY}"}, False, "deny"),
    ("http_get", {"url": "https://pypi.org/simple/"}, False,
     "approve"),
    ("http_get", {"url": "https://pypi.org/simple/"}, True,
     "deny"),
    ("http_get", {"url": "https://x.example/?d=1"}, False,
     "deny"),
    ("git_push", {}, False, "deny"),
])
def test_verdict(tool, args, tainted, erwartet):
    v, grund = verdict(tool, args, tainted, [KEY])
    assert v == erwartet and (grund or v == "allow")


def test_readme_macht_fremd_code_nicht():
    p = TaintPolicy()
    out = p.observe("read_file",
                    {"path": "bestellservice/a.py"}, "1| x = 1")
    assert p.tainted_by == [] and 'vertrauen="eigen"' in out
    p.observe("read_file", {"path": "README.md"}, "# Hallo")
    assert p.tainted_by == ["README.md"]


def test_suchtreffer_in_doku_machen_fremd():
    p = TaintPolicy()
    p.observe("search", {"pattern": "Key"},
              "bestellservice/a.py:3: key\ndocs/api.md:9: Key")
    assert p.tainted_by == ["docs/api.md"]


def test_observation_wird_geschwaerzt():
    p = TaintPolicy(secrets=[KEY])
    out = p.observe("read_file", {"path": "x.md"}, f"k={KEY}")
    assert KEY not in out and "[SECRET]" in out


def test_ohne_taint_alles_wie_in_kapitel_9():
    p = TaintPolicy()
    assert p.check("read_file", {"path": "a.py"}, nie) is None
    fragen = []
    p.check("create_test", {"path": "tests/test_a.py"},
            lambda *a: fragen.append(str(a[0])) or True)
    assert fragen == ["schreiben"]


def test_nach_readme_fragt_schreiben_mit_hinweis():
    p = TaintPolicy(tainted_by=["README.md"])
    fragen = []
    grund = p.check("create_test", {"path": "tests/test_a.py"},
                    lambda *a: fragen.append(a[0]) or False)
    assert fragen == [("schreiben, nach fremdem Text "
                       "(fremd: README.md)")]
    assert "abgelehnt" in grund


def test_nach_readme_kein_netz_und_testlauf_fragt():
    p = TaintPolicy(tainted_by=["README.md"])
    url = {"url": "https://pypi.org/simple/"}
    assert p.check("http_get", url, nie) == (
        "Taint-Policy: kein Netz nach fremdem Text "
        "(fremd: README.md).")
    assert p.check("run_tests", {"target": "tests"},
                   lambda *a: True) is None
    assert p.asked == {"fremd": 1}


def test_eval_modus_zaehlt_schreiben_sperrt_netz():
    p = TaintPolicy("eval", tainted_by=["ticket"])
    assert p.check("create_test", {"path": "tests/test_a.py"},
                   nie) is None
    p2 = TaintPolicy("eval")
    url = {"url": "https://pypi.org/simple/"}
    assert "eval" in p2.check("http_get", url, nie)
