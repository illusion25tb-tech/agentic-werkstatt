"""Gemeinsame Fixtures: frische App je Test, feste Uhr."""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from bestellservice.main import create_app


class StepClock:
    """Uhr, die bei jedem Aufruf eine Minute weiterläuft."""

    def __init__(self, start: datetime):
        self.now = start

    def __call__(self) -> datetime:
        self.now += timedelta(minutes=1)
        return self.now


ADDRESS = {
    "name": "Erika Musterfrau",
    "street": "Musterstraße 1",
    "postal_code": "33602",
    "city": "Bielefeld",
    "country": "DE",
}

CUSTOMER = {
    "name": "Erika Musterfrau",
    "email": "erika@example.org",
    "type": "private",
}


@pytest.fixture
def clock():
    return StepClock(datetime(2026, 10, 19, 8, 0))


@pytest.fixture
def app(clock):
    return create_app(clock=clock)


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def conn(app):
    return app.state.conn


def fill_cart(client, items) -> int:
    """Legt einen Warenkorb mit (sku, menge)-Paaren an."""
    cart_id = client.post("/carts").json()["cart_id"]
    for sku, quantity in items:
        r = client.post(
            f"/carts/{cart_id}/items",
            json={"sku": sku, "quantity": quantity},
        )
        assert r.status_code == 201, r.text
    return cart_id


def place_order(client, items, address=None, customer=None):
    """Bestellt einen neuen Warenkorb, liefert die Antwort."""
    cart_id = fill_cart(client, items)
    return client.post(
        "/orders",
        json={
            "cart_id": cart_id,
            "customer": customer or CUSTOMER,
            "address": address or ADDRESS,
        },
    )


def paid_order(client, items, **kwargs) -> dict:
    """Bestellung anlegen und als bezahlt markieren."""
    r = place_order(client, items, **kwargs)
    assert r.status_code == 201, r.text
    order_id = r.json()["id"]
    r = client.post(
        f"/orders/{order_id}/status", json={"status": "paid"}
    )
    assert r.status_code == 200, r.text
    return r.json()
