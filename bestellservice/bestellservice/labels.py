"""Versandlabels im Datensatzformat von PaketFix.

Ein Label entsteht erst, wenn eine Bestellung bezahlt ist.
Je Bestellung gibt es genau ein Label (ein Paket).
"""

import sqlite3
from collections.abc import Callable
from datetime import datetime

from . import tariffs, tracking
from .config import SENDER_LINES
from .errors import InvalidState, NotFound

# Zeichen je Adresszeile, wie beim alten Etikettendrucker.
LABEL_LINE_MAX = 30


def _cut(text: str) -> str:
    return text.strip()[:LABEL_LINE_MAX]


def postal_line(postal_code: str, city: str) -> str:
    """Zeile mit Postleitzahl und Ort, z. B. 33602 Bielefeld."""
    # Leerzeichen aus dem Bestellformular entfernen.
    return f"{int(postal_code)} {city}"


def address_lines(order: dict) -> list[str]:
    """Empfängerzeilen für das Label."""
    lines = [
        _cut(order["ship_name"]),
        _cut(order["ship_street"]),
        _cut(
            postal_line(
                order["ship_postal"], order["ship_city"]
            )
        ),
    ]
    if order["ship_country"] != "DE":
        lines.append(order["ship_country"])
    return lines


def _parcel_weight(items: list[dict]) -> float:
    """Paketgewicht in kg aus den Bestellpositionen."""
    weight = 0.0
    for item in items:
        weight += item["weight_kg"]
    return round(weight, 2)


def render(
    order: dict,
    tariff: tariffs.Tariff,
    number: str,
    weight_kg: float,
) -> str:
    """Labeltext, wie ihn der Drucker im Lager erhält."""
    out = ["ABSENDER"]
    out += [f"  {line}" for line in SENDER_LINES]
    out.append("EMPFÄNGER")
    out += [f"  {line}" for line in address_lines(order)]
    out.append(f"PRODUKT  {tariff.code} ({tariff.name})")
    out.append(f"GEWICHT  {weight_kg:.2f} kg".replace(".", ","))
    out.append(f"SENDUNG  {tracking.pretty(number)}")
    out.append(f"REFERENZ Bestellung {order['id']}")
    return "\n".join(out)


def _label_row(conn: sqlite3.Connection, order_id: int):
    return conn.execute(
        "SELECT * FROM labels WHERE order_id = ?", (order_id,)
    ).fetchone()


def label_dict(row: sqlite3.Row) -> dict:
    return {
        "order_id": row["order_id"],
        "tracking_number": row["tracking_number"],
        "tariff_code": row["tariff_code"],
        "weight_kg": row["weight_kg"],
        "text": row["text"],
        "created_at": row["created_at"],
    }


def get_label(conn: sqlite3.Connection, order_id: int) -> dict:
    row = _label_row(conn, order_id)
    if row is None:
        raise NotFound(f"Kein Label für Bestellung {order_id}")
    return label_dict(row)


def create_label(
    conn: sqlite3.Connection,
    order: dict,
    clock: Callable[[], datetime] = datetime.now,
) -> dict:
    """Erzeugt das Label für eine bezahlte Bestellung."""
    if order["status"] != "paid":
        raise InvalidState(
            "Label nur für bezahlte Bestellungen "
            f"(Status: {order['status']})"
        )
    if _label_row(conn, order["id"]) is not None:
        raise InvalidState(
            f"Bestellung {order['id']} hat schon ein Label"
        )
    weight = _parcel_weight(order["items"])
    tariff = tariffs.tariff_for(weight)
    cur = conn.execute(
        "INSERT INTO labels (order_id, tracking_number, "
        "tariff_code, weight_kg, text, created_at) "
        "VALUES (?, '', ?, ?, '', ?)",
        (
            order["id"],
            tariff.code,
            weight,
            clock().isoformat(timespec="seconds"),
        ),
    )
    number = tracking.make_tracking_number(cur.lastrowid)
    text = render(order, tariff, number, weight)
    conn.execute(
        "UPDATE labels SET tracking_number = ?, text = ? "
        "WHERE id = ?",
        (number, text, cur.lastrowid),
    )
    conn.commit()
    return get_label(conn, order["id"])
