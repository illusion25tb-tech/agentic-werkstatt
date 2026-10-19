import pytest

from bestellservice import inventory
from bestellservice.errors import OutOfStock, ValidationFailed


def test_available_after_seed(conn):
    assert inventory.available(conn, "WB-200") == 4


def test_reserve_reduces_available(conn):
    inventory.reserve(conn, [("WB-200", 3)])
    info = inventory.stock_info(conn, "WB-200")
    assert info == {
        "sku": "WB-200",
        "on_hand": 4,
        "reserved": 3,
        "available": 1,
    }


def test_reserve_too_much(conn):
    with pytest.raises(OutOfStock):
        inventory.reserve(conn, [("AL-3", 3)])
    assert inventory.available(conn, "AL-3") == 2


def test_release(conn):
    inventory.reserve(conn, [("KS-254", 2)])
    inventory.release(conn, [("KS-254", 2)])
    assert inventory.available(conn, "KS-254") == 3


def test_release_never_negative(conn):
    inventory.release(conn, [("KS-254", 5)])
    info = inventory.stock_info(conn, "KS-254")
    assert info["reserved"] == 0


def test_ship_books_out(conn):
    inventory.reserve(conn, [("AKS-18", 2)])
    inventory.ship(conn, [("AKS-18", 2)])
    info = inventory.stock_info(conn, "AKS-18")
    assert info["on_hand"] == 38
    assert info["reserved"] == 0


def test_inventory_count(conn):
    info = inventory.set_on_hand(conn, "ZS-2", 10)
    assert info["available"] == 10


def test_inventory_count_below_reserved(conn):
    inventory.reserve(conn, [("ZS-2", 5)])
    with pytest.raises(ValidationFailed):
        inventory.set_on_hand(conn, "ZS-2", 4)


def test_inventory_count_negative(conn):
    with pytest.raises(ValidationFailed):
        inventory.set_on_hand(conn, "ZS-2", -1)


def test_api_stock(client):
    r = client.put("/stock/SK-24", json={"on_hand": 7})
    assert r.status_code == 200
    assert client.get("/stock/SK-24").json()["available"] == 7


def test_api_stock_unknown(client):
    assert client.get("/stock/NOPE").status_code == 404
