"""Versteckter Test NL-114: Bestand nach Zahlungsausfall."""

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


def _order(client, sku: str, qty: int) -> int:
    cart_id = client.post("/carts").json()["cart_id"]
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
    return r.json()["id"]


def _set(client, order_id: int, status: str):
    return client.post(
        f"/orders/{order_id}/status", json={"status": status}
    )


def test_payment_failed_releases_stock():
    client = TestClient(create_app())
    order_id = _order(client, "WB-200", 3)
    stock = client.get("/stock/WB-200").json()
    assert stock["available"] == 1
    assert _set(client, order_id, "payment_failed").is_success
    stock = client.get("/stock/WB-200").json()
    assert stock["reserved"] == 0
    assert stock["available"] == 4


def test_released_stock_can_be_ordered_again():
    client = TestClient(create_app())
    first = _order(client, "AL-3", 2)
    _set(client, first, "payment_failed")
    _order(client, "AL-3", 2)
    stock = client.get("/stock/AL-3").json()
    assert stock["available"] == 0


def test_paid_order_keeps_reservation():
    client = TestClient(create_app())
    order_id = _order(client, "WB-200", 1)
    _set(client, order_id, "paid")
    stock = client.get("/stock/WB-200").json()
    assert stock["reserved"] == 1
