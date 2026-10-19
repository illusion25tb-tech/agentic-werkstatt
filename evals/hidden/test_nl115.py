"""Versteckter Test NL-115: Versandkosten nach Österreich."""

from fastapi.testclient import TestClient

from bestellservice.main import create_app
from bestellservice.shipping_costs import shipping_cost


def _shipping(sku: str, country: str) -> float:
    client = TestClient(create_app())
    cart_id = client.post("/carts").json()["cart_id"]
    client.post(
        f"/carts/{cart_id}/items",
        json={"sku": sku, "quantity": 1},
    )
    r = client.get(
        f"/carts/{cart_id}", params={"country": country}
    )
    assert r.status_code == 200
    return r.json()["shipping"]


def test_austria_small_cart():
    assert _shipping("HAM-300", "AT") == 9.90


def test_austria_no_free_shipping():
    assert _shipping("AKS-18", "AT") == 9.90


def test_switzerland():
    assert shipping_cost(30.0, "CH") == 14.90


def test_germany_unchanged():
    assert _shipping("HAM-300", "DE") == 4.95
