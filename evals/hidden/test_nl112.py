"""Versteckter Test NL-112: Suche findet Wortteile."""

from fastapi.testclient import TestClient

from bestellservice.main import create_app


def _skus(query: str) -> set[str]:
    client = TestClient(create_app())
    r = client.get("/articles", params={"q": query})
    assert r.status_code == 200
    return {a["sku"] for a in r.json()}


def test_saege_finds_all_saws():
    assert _skus("säge") == {"HS-550", "SGS-K", "KS-254"}


def test_capitalized_query():
    assert _skus("Säge") == {"HS-550", "SGS-K", "KS-254"}


def test_prefix_search_still_works():
    assert _skus("Akku") == {"AKS-18"}


def test_word_inside_name():
    assert "SR-180" in _skus("regal")
