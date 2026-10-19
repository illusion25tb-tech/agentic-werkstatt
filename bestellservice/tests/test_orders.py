import pytest
from conftest import (
    ADDRESS,
    CUSTOMER,
    fill_cart,
    paid_order,
    place_order,
)

from bestellservice import orders
from bestellservice.errors import ValidationFailed


def test_create_order(client):
    r = place_order(client, [("AKS-18", 1), ("BIT-32", 2)])
    assert r.status_code == 201
    order = r.json()
    assert order["id"] == 10230
    assert order["status"] == "new"
    assert order["total"] == 114.90
    assert len(order["items"]) == 2
    assert order["created_at"] == "19.10.2026 08:02:00"


def test_order_reserves_stock(client):
    place_order(client, [("WB-200", 2)])
    info = client.get("/stock/WB-200").json()
    assert info["reserved"] == 2
    assert info["available"] == 2


def test_order_more_than_stock(client):
    r = place_order(client, [("AL-3", 5)])
    assert r.status_code == 409
    assert "AL-3" in r.json()["detail"]


def test_empty_cart_cannot_be_ordered(client):
    cart_id = client.post("/carts").json()["cart_id"]
    r = client.post(
        "/orders",
        json={
            "cart_id": cart_id,
            "customer": CUSTOMER,
            "address": ADDRESS,
        },
    )
    assert r.status_code == 422


def test_cart_only_once(client):
    cart_id = fill_cart(client, [("ZS-2", 1)])
    body = {
        "cart_id": cart_id,
        "customer": CUSTOMER,
        "address": ADDRESS,
    }
    assert client.post("/orders", json=body).status_code == 201
    assert client.post("/orders", json=body).status_code == 409


def test_get_order(client):
    order_id = place_order(client, [("ZS-2", 1)]).json()["id"]
    order = client.get(f"/orders/{order_id}").json()
    assert order["customer_name"] == "Erika Musterfrau"
    assert order["tracking_number"] is None


def test_unknown_order(client):
    assert client.get("/orders/1").status_code == 404


def test_list_orders_newest_first(client):
    first = place_order(client, [("ZS-2", 1)]).json()["id"]
    second = place_order(client, [("ZS-2", 1)]).json()["id"]
    listed = [o["id"] for o in client.get("/orders").json()]
    assert listed == [second, first]


def test_order_weight():
    items = [
        {"weight_kg": 1.6, "quantity": 2},
        {"weight_kg": 0.3, "quantity": 1},
    ]
    assert orders.order_weight(items) == 3.5


def test_bulky_flag(client):
    order = place_order(client, [("WB-200", 1)]).json()
    assert order["weight_kg"] == 38.0
    assert order["bulky"] is True


@pytest.mark.parametrize(
    "field,value",
    [
        ("postal_code", "3360"),
        ("postal_code", "3360A"),
        ("country", "FR"),
        ("street", "  "),
    ],
)
def test_invalid_address(field, value):
    address = dict(ADDRESS, **{field: value})
    with pytest.raises(ValidationFailed):
        orders.validate_address(address)


def test_austrian_postal_code():
    address = dict(ADDRESS, postal_code="1010", country="at")
    result = orders.validate_address(address)
    assert result["country"] == "AT"


def test_invalid_customer():
    with pytest.raises(ValidationFailed):
        orders.validate_customer(dict(CUSTOMER, email="kein"))
    with pytest.raises(ValidationFailed):
        orders.validate_customer(dict(CUSTOMER, type="vip"))


def test_status_paid(client):
    order = paid_order(client, [("ZS-2", 1)])
    assert order["status"] == "paid"


def test_status_payment_failed(client):
    r = place_order(client, [("ZS-2", 1)])
    order_id = r.json()["id"]
    r = client.post(
        f"/orders/{order_id}/status",
        json={"status": "payment_failed"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "payment_failed"


def test_invalid_transition(client):
    order_id = place_order(client, [("ZS-2", 1)]).json()["id"]
    r = client.post(
        f"/orders/{order_id}/status", json={"status": "shipped"}
    )
    assert r.status_code == 409


def test_unknown_status(client):
    order_id = place_order(client, [("ZS-2", 1)]).json()["id"]
    r = client.post(
        f"/orders/{order_id}/status", json={"status": "weg"}
    )
    assert r.status_code == 422


def test_ship_needs_label(client):
    order = paid_order(client, [("ZS-2", 1)])
    r = client.post(
        f"/orders/{order['id']}/status",
        json={"status": "shipped"},
    )
    assert r.status_code == 409


def test_ship_with_label(client):
    order = paid_order(client, [("AKS-18", 1)])
    client.post(f"/orders/{order['id']}/label")
    r = client.post(
        f"/orders/{order['id']}/status",
        json={"status": "shipped"},
    )
    assert r.status_code == 200
    info = client.get("/stock/AKS-18").json()
    assert info["on_hand"] == 39
    assert info["reserved"] == 0


def test_history(client):
    order = paid_order(client, [("ZS-2", 1)])
    history = client.get(
        f"/orders/{order['id']}/history"
    ).json()
    assert history[0]["old_status"] == "new"
    assert history[0]["new_status"] == "paid"


def test_confirmation_private(client):
    order_id = place_order(client, [("AKS-18", 1)]).json()["id"]
    text = client.get(f"/orders/{order_id}/confirmation").text
    assert "Bestellnummer: 10230" in text
    assert "89,90 EUR (inkl. 19 % MwSt.)" in text
    assert "kostenlos" in text


def test_confirmation_mentions_bulky(client):
    order_id = place_order(client, [("SR-180", 1)]).json()["id"]
    text = client.get(f"/orders/{order_id}/confirmation").text
    assert "Sperrgut" in text


def test_service_summary(client):
    order_id = place_order(client, [("AKS-18", 1)]).json()["id"]
    order = client.get(f"/orders/{order_id}").json()
    line = orders.service_summary(order)
    assert line.startswith("#10230 Erika Musterfrau | new")
    assert line.endswith("kein Label")


def test_export_csv(client):
    place_order(client, [("AKS-18", 1)])
    text = client.get("/orders/export.csv").text
    header, row = text.strip().splitlines()
    assert header.startswith("id;created_at")
    assert ";89,90" in row


def test_revenue_by_status(client, conn):
    place_order(client, [("AKS-18", 1)])
    paid_order(client, [("HAM-300", 1)])
    report = orders.revenue_by_status(conn)
    assert report["new"]["revenue"] == 89.90
    assert report["paid"]["orders"] == 1
