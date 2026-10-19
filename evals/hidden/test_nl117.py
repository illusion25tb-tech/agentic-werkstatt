"""Versteckter Test NL-117: Adresszeilen bis 35 Zeichen."""

from fastapi.testclient import TestClient

from bestellservice import labels
from bestellservice.main import create_app

CUSTOMER = {
    "name": "Erika Musterfrau",
    "email": "erika@example.org",
}

# 33 Zeichen; PaketFix erlaubt laut Spezifikation 35.
STREET = "Musterstraße 12, Hinterhaus links"


def _paid_order(client, address: dict) -> int:
    cart_id = client.post("/carts").json()["cart_id"]
    client.post(
        f"/carts/{cart_id}/items",
        json={"sku": "AKS-18", "quantity": 1},
    )
    body = {
        "cart_id": cart_id,
        "customer": CUSTOMER,
        "address": address,
    }
    r = client.post("/orders", json=body)
    assert r.status_code == 201, r.text
    order_id = r.json()["id"]
    client.post(
        f"/orders/{order_id}/status", json={"status": "paid"}
    )
    return order_id


def test_street_of_33_chars_is_complete():
    assert len(STREET) == 33
    client = TestClient(create_app())
    address = {
        "name": "Erika Musterfrau",
        "street": STREET,
        "postal_code": "33602",
        "city": "Bielefeld",
    }
    order_id = _paid_order(client, address)
    label = client.post(f"/orders/{order_id}/label").json()
    assert f"  {STREET}" in label["text"].splitlines()


def test_long_name_is_cut_at_35():
    order = {
        "ship_name": "Werkstatt Musterfrau und Beispiel GbR",
        "ship_street": "Musterweg 1",
        "ship_postal": "33602",
        "ship_city": "Bielefeld",
        "ship_country": "DE",
    }
    lines = labels.address_lines(order)
    assert lines[0] == "Werkstatt Musterfrau und Beispiel G"
    assert len(lines[0]) == 35
