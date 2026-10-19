"""Versteckter Test NL-116: Bestellübersicht nach Datum."""

from datetime import datetime

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


class ListClock:
    """Liefert der Reihe nach vorgegebene Zeitpunkte."""

    def __init__(self, moments: list[datetime]):
        self.moments = list(moments)
        self.last = moments[0]

    def __call__(self) -> datetime:
        if self.moments:
            self.last = self.moments.pop(0)
        return self.last


def _order(client) -> int:
    cart_id = client.post("/carts").json()["cart_id"]
    client.post(
        f"/carts/{cart_id}/items",
        json={"sku": "ZS-2", "quantity": 1},
    )
    body = {
        "cart_id": cart_id,
        "customer": CUSTOMER,
        "address": ADDRESS,
    }
    r = client.post("/orders", json=body)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _created_and_listed(*moments: datetime):
    # Jede Bestellung liest die Uhr zweimal:
    # beim Warenkorb und bei der Bestellung.
    ticks = [m for m in moments for _ in range(2)]
    app = create_app(clock=ListClock(ticks))
    client = TestClient(app)
    created = [_order(client) for _ in moments]
    listed = [o["id"] for o in client.get("/orders").json()]
    return created, listed


def test_newest_first_across_months():
    created, listed = _created_and_listed(
        datetime(2026, 9, 30, 10, 0),
        datetime(2026, 10, 2, 9, 0),
    )
    assert listed == [created[1], created[0]]


def test_newest_first_across_years():
    created, listed = _created_and_listed(
        datetime(2025, 12, 31, 23, 50),
        datetime(2026, 1, 1, 0, 10),
        datetime(2026, 1, 15, 8, 0),
    )
    assert listed == list(reversed(created))
