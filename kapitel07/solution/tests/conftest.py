"""Acceptance Tests laufen gegen den echten bestellservice.

Er wird importiert, nicht kopiert und nicht verändert.
"""
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BS = Path(os.environ.get(
    "BESTELLSERVICE", Path(__file__).parents[3]
    / "bestellservice")).resolve()
sys.path.insert(0, str(BS))

from bestellservice.main import create_app

MAIL = "erika@example.org"
KUNDE = {"name": "Erika Musterfrau", "email": MAIL}
ADRESSE = {"name": "Erika Musterfrau",
           "street": "Musterstraße 1",
           "postal_code": "33602", "city": "Bielefeld"}


@pytest.fixture
def client():
    return TestClient(create_app())


@pytest.fixture
def bestellung(client):
    """Legt eine Bestellung mit 2 x AKS-18 an, Status new."""
    def anlegen(status="new", label=False) -> int:
        cart = client.post("/carts").json()["cart_id"]
        client.post(f"/carts/{cart}/items",
                    json={"sku": "AKS-18", "quantity": 2})
        oid = client.post("/orders", json={
            "cart_id": cart, "customer": KUNDE,
            "address": ADRESSE}).json()["id"]
        if status != "new":
            client.post(f"/orders/{oid}/status",
                        json={"status": status})
        if label:
            client.post(f"/orders/{oid}/label")
        return oid
    return anlegen
