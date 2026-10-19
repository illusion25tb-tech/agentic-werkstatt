"""Versteckter Test NL-111: Gutscheincode kleingeschrieben."""

import pytest
from fastapi.testclient import TestClient

from bestellservice.main import create_app


def _cart(client) -> int:
    cart_id = client.post("/carts").json()["cart_id"]
    client.post(
        f"/carts/{cart_id}/items",
        json={"sku": "AKS-18", "quantity": 1},
    )
    return cart_id


@pytest.mark.parametrize(
    "code", ["nordlicht10", "Nordlicht10", " NORDLICHT10 "]
)
def test_coupon_ignores_case_and_spaces(code):
    client = TestClient(create_app())
    cart_id = _cart(client)
    r = client.post(
        f"/carts/{cart_id}/coupon", json={"code": code}
    )
    assert r.status_code == 200
    summary = client.get(f"/carts/{cart_id}").json()
    assert summary["coupon_code"] == "NORDLICHT10"
    assert summary["discount"] == 8.99


def test_unknown_code_still_rejected():
    client = TestClient(create_app())
    cart_id = _cart(client)
    r = client.post(
        f"/carts/{cart_id}/coupon", json={"code": "gratis"}
    )
    assert r.status_code == 422
