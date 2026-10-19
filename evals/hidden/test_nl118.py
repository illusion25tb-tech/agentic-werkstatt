"""Versteckter Test NL-118: Staffelpreis ab der Staffelmenge."""

from fastapi.testclient import TestClient

from bestellservice import catalog
from bestellservice.main import create_app


def _unit_price(sku: str, qty: int) -> float:
    client = TestClient(create_app())
    cart_id = client.post("/carts").json()["cart_id"]
    client.post(
        f"/carts/{cart_id}/items",
        json={"sku": sku, "quantity": qty},
    )
    lines = client.get(f"/carts/{cart_id}").json()["lines"]
    return lines[0]["unit_price"]


def test_exactly_ten_screws_get_bulk_price():
    assert _unit_price("SCH-440", 10) == 8.95


def test_exactly_ten_gloves_get_bulk_price():
    assert _unit_price("AH-10", 10) == 4.25


def test_nine_pay_normal_price():
    assert _unit_price("SCH-440", 9) == 9.95


def test_unit_price_function():
    article = catalog.Article(
        sku="X",
        name="X",
        category="X",
        price=2.0,
        weight_kg=0.1,
        bulk_from=5,
        bulk_price=1.5,
    )
    assert catalog.unit_price(article, 5) == 1.5
    assert catalog.unit_price(article, 4) == 2.0
