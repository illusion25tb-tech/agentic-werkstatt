from conftest import ADDRESS, paid_order, place_order

from bestellservice import labels, tracking


def test_label_for_paid_order(client):
    order = paid_order(client, [("AKS-18", 1)])
    r = client.post(f"/orders/{order['id']}/label")
    assert r.status_code == 201
    label = r.json()
    assert label["tariff_code"] == "PF-STD-S"
    assert label["weight_kg"] == 1.6
    assert tracking.is_valid(label["tracking_number"])


def test_label_text(client):
    order = paid_order(client, [("AKS-18", 1)])
    label = client.post(f"/orders/{order['id']}/label").json()
    text = label["text"]
    assert "Nordlicht Werkzeughandel GmbH" in text
    assert "  Erika Musterfrau" in text
    assert "  33602 Bielefeld" in text
    assert "GEWICHT  1,60 kg" in text
    assert f"REFERENZ Bestellung {order['id']}" in text


def test_label_needs_payment(client):
    order_id = place_order(client, [("AKS-18", 1)]).json()["id"]
    r = client.post(f"/orders/{order_id}/label")
    assert r.status_code == 409


def test_only_one_label(client):
    order = paid_order(client, [("AKS-18", 1)])
    client.post(f"/orders/{order['id']}/label")
    r = client.post(f"/orders/{order['id']}/label")
    assert r.status_code == 409


def test_get_label(client):
    order = paid_order(client, [("AKS-18", 1)])
    created = client.post(f"/orders/{order['id']}/label").json()
    fetched = client.get(f"/orders/{order['id']}/label").json()
    assert fetched == created


def test_missing_label(client):
    order = paid_order(client, [("AKS-18", 1)])
    r = client.get(f"/orders/{order['id']}/label")
    assert r.status_code == 404


def test_tracking_number_on_order(client):
    order = paid_order(client, [("AKS-18", 1)])
    label = client.post(f"/orders/{order['id']}/label").json()
    again = client.get(f"/orders/{order['id']}").json()
    assert again["tracking_number"] == label["tracking_number"]


def test_medium_parcel(client):
    order = paid_order(client, [("AL-3", 1)])
    label = client.post(f"/orders/{order['id']}/label").json()
    assert label["tariff_code"] == "PF-STD-L"


def test_heavy_standard_parcel(client):
    order = paid_order(client, [("ZE-25", 1), ("SK-24", 1)])
    label = client.post(f"/orders/{order['id']}/label").json()
    assert label["weight_kg"] == 27.1
    assert label["tariff_code"] == "PF-STD-XL"


def test_foreign_address_shows_country(client):
    address = dict(
        ADDRESS, postal_code="8010", city="Graz", country="AT"
    )
    order = paid_order(client, [("AKS-18", 1)], address=address)
    label = client.post(f"/orders/{order['id']}/label").json()
    assert label["text"].splitlines()[-5] == "  AT"


def test_postal_line():
    assert labels.postal_line("33602", "Bielefeld") == (
        "33602 Bielefeld"
    )


def test_address_lines_domestic():
    order = {
        "ship_name": "Max Mustermann",
        "ship_street": "Beispielweg 5",
        "ship_postal": "80331",
        "ship_city": "München",
        "ship_country": "DE",
    }
    assert labels.address_lines(order) == [
        "Max Mustermann",
        "Beispielweg 5",
        "80331 München",
    ]
