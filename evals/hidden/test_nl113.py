"""Versteckter Test NL-113: Umsatzsteuer auf die Summe."""

from decimal import ROUND_HALF_UP, Decimal

from fastapi.testclient import TestClient

from bestellservice.main import create_app

CUSTOMER = {
    "name": "Erika Musterfrau",
    "email": "erika@example.org",
}
ADDRESS = {
    "name": "Erika Musterfrau",
    "street": "Musterstraße 1",
    "postal_code": "33602",
    "city": "Bielefeld",
}


def _invoice(items) -> dict:
    client = TestClient(create_app())
    cart_id = client.post("/carts").json()["cart_id"]
    for sku, qty in items:
        client.post(
            f"/carts/{cart_id}/items",
            json={"sku": sku, "quantity": qty},
        )
    body = {
        "cart_id": cart_id,
        "customer": CUSTOMER,
        "address": ADDRESS,
    }
    r = client.post("/orders", json=body)
    assert r.status_code == 201, r.text
    order_id = r.json()["id"]
    return client.get(f"/orders/{order_id}/invoice").json()


def _vat(gross: str) -> float:
    vat = Decimal(gross) * 19 / 119
    cent = Decimal("0.01")
    return float(vat.quantize(cent, rounding=ROUND_HALF_UP))


def test_vat_on_total():
    inv = _invoice([("AKS-18", 1), ("SK-24", 1)])
    assert inv["gross"] == 109.89
    assert inv["vat"] == _vat("109.89") == 17.55
    assert inv["net"] == 92.34


def test_vat_with_shipping():
    inv = _invoice([("HAM-300", 1), ("ZS-2", 1)])
    assert inv["gross"] == 26.85
    assert inv["vat"] == _vat("26.85")
    assert round(inv["net"] + inv["vat"], 2) == inv["gross"]


def test_single_item_unchanged():
    inv = _invoice([("AKS-18", 1)])
    assert inv["vat"] == 14.35
