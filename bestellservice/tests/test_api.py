from bestellservice.main import create_app


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_extra_fields_are_rejected(client):
    cart_id = client.post("/carts").json()["cart_id"]
    r = client.post(
        f"/carts/{cart_id}/items",
        json={"sku": "ZS-2", "quantity": 1, "price": 0.01},
    )
    assert r.status_code == 422


def test_apps_do_not_share_data():
    from fastapi.testclient import TestClient

    first = TestClient(create_app())
    second = TestClient(create_app())
    first.post("/carts")
    first.post("/carts")
    r = second.post("/carts")
    assert r.json()["cart_id"] == 1


def test_categories_endpoint(client):
    cats = client.get("/categories").json()
    assert "Baustoffe" in cats


def test_openapi_lists_label_route(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert "/orders/{order_id}/label" in paths
