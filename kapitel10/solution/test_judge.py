"""Geskripteter Judge: gültige Skala oder gar kein Urteil."""
import json

from judge import judge


def antwort(**d):
    return lambda messages: json.dumps(d)


def test_gueltiges_urteil():
    v = judge(antwort(reason="Zeile 8: Rückfall jetzt "
                      "SPERRGUT, Ursache genannt.", score=3),
              "Begründung", "diff")
    assert v.score == 3


def test_ungueltige_skala_und_ohne_grund():
    assert judge(antwort(reason="x" * 30, score=5), "b",
                 "d") is None
    assert judge(antwort(score=4), "b", "d") is None
