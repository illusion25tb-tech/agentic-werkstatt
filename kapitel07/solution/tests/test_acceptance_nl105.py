"""Acceptance Tests zu spec/NL-105.md (S1 bis S6)."""
import pytest
from conftest import MAIL

pytestmark = pytest.mark.xfail(
    strict=True, raises=AssertionError,
    reason="NL-105 ist noch nicht umgesetzt")


def storno(client, oid, mail=MAIL):
    return client.post(f"/orders/{oid}/cancel",
                       json={"email": mail})


@pytest.mark.parametrize("status", ["new", "paid"])
def test_s1_storno_gibt_bestand_frei(client, bestellung,
                                     status):
    r = storno(client, bestellung(status))
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "cancelled"
    assert client.get("/stock/AKS-18").json()["reserved"] == 0


def test_s2_nicht_mehr_mit_label(client, bestellung):
    oid = bestellung("paid", label=True)
    assert storno(client, oid).status_code == 409
    assert client.get(f"/orders/{oid}").json()["status"] \
        == "paid"


def test_s3_nicht_nach_versand(client, bestellung):
    oid = bestellung("paid", label=True)
    client.post(f"/orders/{oid}/status",
                json={"status": "shipped"})
    assert storno(client, oid).status_code == 409


def test_s4_fremde_mail(client, bestellung):
    r = storno(client, bestellung(), mail="max@example.org")
    assert r.status_code == 403


def test_s5_unbekannte_bestellung(client):
    r = storno(client, 99999)
    assert r.status_code == 404
    assert "existiert nicht" in r.json()["detail"]


def test_s6_storno_in_historie(client, bestellung):
    oid = bestellung()
    assert storno(client, oid).status_code == 200
    hist = client.get(f"/orders/{oid}/history").json()
    assert hist[-1]["new_status"] == "cancelled"
