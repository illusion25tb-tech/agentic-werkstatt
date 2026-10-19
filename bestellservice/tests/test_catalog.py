import pytest

from bestellservice import catalog
from bestellservice.errors import NotFound


def test_list_is_sorted_by_sku(conn):
    skus = [a.sku for a in catalog.list_articles(conn)]
    assert skus == sorted(skus)
    assert len(skus) == 20


def test_list_by_category(conn):
    found = catalog.list_articles(conn, "Baustoffe")
    assert {a.sku for a in found} == {"ZE-25", "FK-20"}


def test_get_article(conn):
    article = catalog.get_article(conn, "AKS-18")
    assert article.name == "Akkuschrauber 18 V"
    assert article.price == 89.90


def test_unknown_article(conn):
    with pytest.raises(NotFound):
        catalog.get_article(conn, "GIBT-ES-NICHT")


def test_search_by_name_prefix(conn):
    found = catalog.search(conn, "Akku")
    assert [a.sku for a in found] == ["AKS-18"]


def test_search_ignores_case(conn):
    found = catalog.search(conn, "wASSERwaage")
    assert [a.sku for a in found] == ["WW-120"]


def test_search_by_sku(conn):
    found = catalog.search(conn, "wb-")
    assert [a.sku for a in found] == ["WB-200"]


def test_empty_search(conn):
    assert catalog.search(conn, "   ") == []


def test_unit_price_without_bulk(conn):
    article = catalog.get_article(conn, "SCH-440")
    assert catalog.unit_price(article, 5) == 9.95


def test_unit_price_with_bulk(conn):
    article = catalog.get_article(conn, "SCH-440")
    assert catalog.unit_price(article, 12) == 8.95


def test_article_without_bulk_price(conn):
    article = catalog.get_article(conn, "HS-550")
    assert catalog.unit_price(article, 50) == 24.90


def test_deactivated_article_disappears(conn):
    catalog.deactivate(conn, "ZB-01")
    skus = [a.sku for a in catalog.list_articles(conn)]
    assert "ZB-01" not in skus


def test_categories(conn):
    cats = catalog.categories(conn)
    assert "Elektrowerkzeug" in cats
    assert cats == sorted(cats)


def test_api_articles(client):
    r = client.get("/articles", params={"q": "Zement"})
    assert r.status_code == 200
    assert r.json()[0]["sku"] == "ZE-25"


def test_api_article_not_found(client):
    r = client.get("/articles/XYZ")
    assert r.status_code == 404
    assert "XYZ" in r.json()["detail"]
