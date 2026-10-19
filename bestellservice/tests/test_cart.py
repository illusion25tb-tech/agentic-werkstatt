from conftest import fill_cart

from bestellservice import cart


def test_empty_cart(client):
    cart_id = client.post("/carts").json()["cart_id"]
    summary = client.get(f"/carts/{cart_id}").json()
    assert summary["lines"] == []
    assert summary["total"] == 0.0
    assert summary["shipping"] == 0.0


def test_small_cart_pays_shipping(client):
    cart_id = fill_cart(client, [("HAM-300", 2)])
    summary = client.get(f"/carts/{cart_id}").json()
    assert summary["subtotal"] == 29.90
    assert summary["shipping"] == 4.95
    assert summary["total"] == 34.85
    assert summary["missing_for_free_shipping"] == 20.10


def test_large_cart_ships_free(client):
    cart_id = fill_cart(client, [("AKS-18", 1)])
    summary = client.get(f"/carts/{cart_id}").json()
    assert summary["shipping"] == 0.0
    assert summary["total"] == 89.90
    assert summary["missing_for_free_shipping"] == 0.0


def test_line_total(client):
    cart_id = fill_cart(client, [("BIT-32", 3)])
    line = client.get(f"/carts/{cart_id}").json()["lines"][0]
    assert line["unit_price"] == 12.50
    assert line["line_total"] == 37.50


def test_bulk_price_in_cart(client):
    cart_id = fill_cart(client, [("DUE-6", 20)])
    line = client.get(f"/carts/{cart_id}").json()["lines"][0]
    assert line["unit_price"] == 2.99


def test_remove_item(client):
    cart_id = fill_cart(client, [("ZS-2", 1)])
    summary = client.get(f"/carts/{cart_id}").json()
    item_id = summary["lines"][0]["item_id"]
    r = client.delete(f"/carts/{cart_id}/items/{item_id}")
    assert r.status_code == 200
    assert client.get(f"/carts/{cart_id}").json()["lines"] == []


def test_remove_unknown_item(client):
    cart_id = fill_cart(client, [("ZS-2", 1)])
    r = client.delete(f"/carts/{cart_id}/items/999")
    assert r.status_code == 404


def test_quantity_limits(client):
    cart_id = client.post("/carts").json()["cart_id"]
    r = client.post(
        f"/carts/{cart_id}/items",
        json={"sku": "ZS-2", "quantity": 100},
    )
    assert r.status_code == 422


def test_unknown_cart(client):
    assert client.get("/carts/4242").status_code == 404


def test_percent_coupon(client):
    cart_id = fill_cart(client, [("AKS-18", 1)])
    r = client.post(
        f"/carts/{cart_id}/coupon", json={"code": "NORDLICHT10"}
    )
    assert r.status_code == 200
    summary = client.get(f"/carts/{cart_id}").json()
    assert summary["discount"] == 8.99
    assert summary["total"] == 80.91


def test_amount_coupon_needs_minimum(client):
    cart_id = fill_cart(client, [("AKS-18", 1)])
    client.post(
        f"/carts/{cart_id}/coupon", json={"code": "WERKBANK20"}
    )
    summary = client.get(f"/carts/{cart_id}").json()
    assert summary["discount"] == 0.0


def test_amount_coupon(client):
    cart_id = fill_cart(client, [("WB-200", 1)])
    client.post(
        f"/carts/{cart_id}/coupon", json={"code": "WERKBANK20"}
    )
    summary = client.get(f"/carts/{cart_id}").json()
    assert summary["discount"] == 20.0
    assert summary["total"] == 369.0


def test_invalid_coupon(client):
    cart_id = fill_cart(client, [("AKS-18", 1)])
    r = client.post(
        f"/carts/{cart_id}/coupon", json={"code": "GRATIS"}
    )
    assert r.status_code == 422


def test_unsupported_country(client):
    cart_id = fill_cart(client, [("AKS-18", 1)])
    r = client.get(
        f"/carts/{cart_id}", params={"country": "FR"}
    )
    assert r.status_code == 422


def test_format_eur():
    assert cart.format_eur(1234.5) == "1.234,50 EUR"
    assert cart.format_eur(4.95) == "4,95 EUR"


def test_subtotal_of_lines():
    lines = [
        {"unit_price": 10.0, "quantity": 2},
        {"unit_price": 5.5, "quantity": 1},
    ]
    assert cart.cart_subtotal(lines) == 25.5
