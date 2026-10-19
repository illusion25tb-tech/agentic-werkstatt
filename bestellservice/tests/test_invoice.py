from conftest import place_order

from bestellservice import invoice


def test_invoice_single_item(client):
    order_id = place_order(client, [("AKS-18", 1)]).json()["id"]
    inv = client.get(f"/orders/{order_id}/invoice").json()
    assert inv["number"] == f"RE-2026-{order_id}"
    assert inv["gross"] == 89.90
    assert inv["vat"] == 14.35
    assert inv["net"] == 75.55


def test_invoice_with_shipping(client):
    order_id = place_order(client, [("ZS-2", 1)]).json()["id"]
    inv = client.get(f"/orders/{order_id}/invoice").json()
    texts = [p["text"] for p in inv["positions"]]
    assert texts == ["1 x Zollstock 2 m", "Versand"]
    assert inv["gross"] == 11.90


def test_invoice_display():
    assert invoice.eur(1234.5) == "1.234,50 EUR"


def test_invoice_recipient(client):
    order_id = place_order(client, [("AKS-18", 1)]).json()["id"]
    inv = client.get(f"/orders/{order_id}/invoice").json()
    assert inv["recipient"][-1] == "33602 Bielefeld"
