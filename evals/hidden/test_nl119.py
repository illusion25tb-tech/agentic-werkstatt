"""Versteckter Test NL-119: Prüfziffer nach PaketFix-Verfahren.

Beispiele aus docs/paketfix/paketfix_api_v2.md, Abschnitt
"Sendungsnummer".
"""

from bestellservice import tracking


def test_example_from_spec():
    assert tracking.check_digit("341234567890") == 0
    assert tracking.is_valid("3412345678900")


def test_first_tracking_number():
    number = tracking.make_tracking_number(1)
    assert number == "3400000000012"


def test_number_with_wrong_digit_is_rejected():
    assert not tracking.is_valid("3400000000016")
