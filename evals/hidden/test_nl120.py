"""Versteckter Test NL-120: Labelgewicht mit Stückzahl."""

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


def _label(items) -> dict:
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
    order = client.post("/orders", json=body).json()
    client.post(
        f"/orders/{order['id']}/status",
        json={"status": "paid"},
    )
    url = f"/orders/{order['id']}/label"
    label = client.post(url).json()
    label["order_weight"] = order["weight_kg"]
    return label


def test_label_weight_counts_quantity():
    label = _label([("AKS-18", 2), ("BIT-32", 1)])
    assert label["weight_kg"] == 3.5
    assert "GEWICHT  3,50 kg" in label["text"]


def test_label_matches_order_weight():
    label = _label([("FK-20", 1), ("HL-750", 3)])
    assert label["weight_kg"] == label["order_weight"]
    assert label["weight_kg"] == 22.4
    assert label["tariff_code"] == "PF-STD-XL"
