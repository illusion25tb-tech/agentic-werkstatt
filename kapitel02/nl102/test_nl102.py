"""Regressionstest NL-102: führende Null der PLZ bleibt."""

from conftest import ADDRESS, paid_order

from bestellservice import labels


def test_leading_zero_is_kept():
    line = labels.postal_line("01067", "Dresden")
    assert line == "01067 Dresden"


def test_postal_code_without_leading_zero():
    line = labels.postal_line("33602", "Bielefeld")
    assert line == "33602 Bielefeld"


def test_label_for_dresden(client):
    address = dict(ADDRESS, postal_code="01067", city="Dresden")
    order = paid_order(client, [("AKS-18", 1)], address=address)
    label = client.post(f"/orders/{order['id']}/label").json()
    assert "  01067 Dresden" in label["text"].splitlines()
