"""Rechnungsdaten zu einer Bestellung.

Alle Katalogpreise sind Bruttopreise. Die Rechnung weist
Netto, Umsatzsteuer und Brutto aus.
"""

import sqlite3

from . import orders
from .config import SENDER_LINES, VAT_PERCENT


def eur(value: float) -> str:
    """Formatiert einen Betrag als 1.234,50 EUR."""
    s = "{:,.2f}".format(value)
    s = s.replace(",", "_").replace(".", ",").replace("_", ".")
    return s + " EUR"


def _vat_from_gross(gross: float) -> float:
    return round(gross * VAT_PERCENT / (100 + VAT_PERCENT), 2)


def invoice_number(order: dict) -> str:
    year = order["created_at"][6:10]
    return f"RE-{year}-{order['id']}"


def build_invoice(
    conn: sqlite3.Connection, order_id: int
) -> dict:
    """Rechnungsdaten mit Positionen und Steuerausweis."""
    order = orders.get_order(conn, order_id)
    positions = []
    for item in order["items"]:
        gross = round(item["unit_price"] * item["quantity"], 2)
        positions.append(
            {
                "text": f"{item['quantity']} x {item['name']}",
                "gross": gross,
                "vat": _vat_from_gross(gross),
            }
        )
    if order["discount"]:
        gross = -order["discount"]
        positions.append(
            {
                "text": "Gutschein",
                "gross": gross,
                "vat": _vat_from_gross(gross),
            }
        )
    if order["shipping"]:
        positions.append(
            {
                "text": "Versand",
                "gross": order["shipping"],
                "vat": _vat_from_gross(order["shipping"]),
            }
        )
    gross_total = round(sum(p["gross"] for p in positions), 2)
    vat_total = round(sum(p["vat"] for p in positions), 2)
    return {
        "number": invoice_number(order),
        "order_id": order_id,
        "issuer": list(SENDER_LINES),
        "recipient": [
            order["customer_name"],
            order["ship_street"],
            f"{order['ship_postal']} {order['ship_city']}",
        ],
        "positions": positions,
        "gross": gross_total,
        "vat": vat_total,
        "net": round(gross_total - vat_total, 2),
        "vat_percent": VAT_PERCENT,
        "display": {
            "gross": eur(gross_total),
            "vat": eur(vat_total),
            "net": eur(gross_total - vat_total),
        },
    }
